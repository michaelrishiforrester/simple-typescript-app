#!/usr/bin/env python3
"""
Automated Patching Test Script

This script automates the testing of the patch compliance monitoring and automated remediation solution.
It creates non-compliant conditions, forces evaluation, and monitors the automated remediation process.
"""

import argparse
import boto3
import json
import time
import sys
from datetime import datetime

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Test the automated patching solution.')
    parser.add_argument('--instance-id', required=True, help='The EC2 instance ID to test')
    parser.add_argument('--region', default='us-east-1', help='AWS region (default: us-east-1)')
    parser.add_argument('--rule-name', default='ec2-managedinstance-patch-compliance-status-check', 
                        help='AWS Config rule name (default: ec2-managedinstance-patch-compliance-status-check)')
    parser.add_argument('--wait-time', type=int, default=300, 
                        help='Time to wait for automation to complete in seconds (default: 300)')
    return parser.parse_args()

def init_clients(region):
    """Initialize AWS service clients."""
    ssm = boto3.client('ssm', region_name=region)
    config = boto3.client('config', region_name=region)
    ec2 = boto3.client('ec2', region_name=region)
    events = boto3.client('events', region_name=region)
    logs = boto3.client('logs', region_name=region)
    return ssm, config, ec2, events, logs

def check_instance_managed(ssm, instance_id):
    """Check if the instance is managed by SSM."""
    print(f"Checking if instance {instance_id} is managed by SSM...")
    try:
        response = ssm.describe_instance_information(
            Filters=[{'Key': 'InstanceIds', 'Values': [instance_id]}]
        )
        if response['InstanceInformationList']:
            print(f"✅ Instance {instance_id} is managed by SSM")
            return True
        else:
            print(f"❌ Instance {instance_id} is NOT managed by SSM")
            return False
    except Exception as e:
        print(f"❌ Error checking instance management status: {e}")
        return False

def create_non_compliant_state(ssm, instance_id):
    """Create a non-compliant patch state by scanning for patches."""
    print(f"Creating non-compliant state by scanning for patches on {instance_id}...")
    try:
        response = ssm.send_command(
            DocumentName='AWS-RunPatchBaseline',
            DocumentVersion='$DEFAULT',
            Targets=[{'Key': 'InstanceIds', 'Values': [instance_id]}],
            Parameters={'Operation': ['Scan']},
            TimeoutSeconds=600
        )
        command_id = response['Command']['CommandId']
        print(f"Scan command initiated with ID: {command_id}")
        
        # Wait for command to complete
        print("Waiting for scan to complete...")
        waiter = ssm.get_waiter('command_executed')
        waiter.wait(
            CommandId=command_id,
            InstanceId=instance_id,
            WaiterConfig={'Delay': 5, 'MaxAttempts': 30}
        )
        print("✅ Patch scan completed")
        return True
    except Exception as e:
        print(f"❌ Error creating non-compliant state: {e}")
        return False

def force_config_evaluation(config, rule_name):
    """Force AWS Config to evaluate the patch compliance rule."""
    print(f"Forcing evaluation of AWS Config rule: {rule_name}...")
    try:
        response = config.start_config_rules_evaluation(
            ConfigRuleNames=[rule_name]
        )
        print(f"✅ Evaluation started: {response}")
        return True
    except Exception as e:
        print(f"❌ Error starting config evaluation: {e}")
        return False

def check_compliance_status(config, rule_name, instance_id):
    """Check the compliance status of the instance for the specified rule."""
    print(f"Checking compliance status of {instance_id} for rule {rule_name}...")
    try:
        response = config.get_compliance_details_by_resource(
            ResourceType='AWS::EC2::Instance',
            ResourceId=instance_id,
            ComplianceTypes=['NON_COMPLIANT', 'COMPLIANT'],
            Limit=10
        )
        
        for eval_result in response.get('EvaluationResults', []):
            if eval_result['EvaluationResultIdentifier']['EvaluationResultQualifier']['ConfigRuleName'] == rule_name:
                status = eval_result['ComplianceType']
                print(f"✅ Compliance status: {status}")
                return status
        
        print("❓ No compliance result found for this rule and instance")
        return None
    except Exception as e:
        print(f"❌ Error checking compliance status: {e}")
        return None

def check_automation_execution(ssm, instance_id):
    """Check if any automation execution is running for the instance."""
    print(f"Checking for automation executions for instance {instance_id}...")
    try:
        response = ssm.describe_automation_executions(
            Filters=[
                {
                    'Key': 'DocumentNamePrefix',
                    'Values': ['AWS-RunPatchBaseline']
                }
            ]
        )
        
        found = False
        for execution in response['AutomationExecutions']:
            if 'Target' in execution['ExecutionStartTime']:
                targets = execution['Target']
                if instance_id in str(targets):
                    print(f"✅ Found automation execution: {execution['AutomationExecutionId']}")
                    print(f"   Status: {execution['AutomationExecutionStatus']}")
                    print(f"   Started: {execution['ExecutionStartTime']}")
                    found = True
                    return execution['AutomationExecutionId']
        
        if not found:
            print("❓ No automation execution found for this instance")
            return None
    except Exception as e:
        print(f"❌ Error checking automation executions: {e}")
        return None

def wait_for_automation(ssm, execution_id, wait_time):
    """Wait for an automation execution to complete."""
    if not execution_id:
        return None
        
    print(f"Waiting for automation execution {execution_id} to complete...")
    timeout = time.time() + wait_time
    status = None
    
    while time.time() < timeout:
        try:
            response = ssm.describe_automation_executions(
                Filters=[
                    {
                        'Key': 'ExecutionId',
                        'Values': [execution_id]
                    }
                ]
            )
            
            if response['AutomationExecutions']:
                status = response['AutomationExecutions'][0]['AutomationExecutionStatus']
                print(f"Current status: {status}")
                
                if status in ['Success', 'Failed', 'TimedOut', 'Cancelled']:
                    break
            
            time.sleep(30)
        except Exception as e:
            print(f"❌ Error checking automation status: {e}")
            time.sleep(30)
    
    if status == 'Success':
        print(f"✅ Automation completed successfully")
    else:
        print(f"⚠️ Automation ended with status: {status}")
    
    return status

def check_patch_state(ssm, instance_id):
    """Check the current patch state of the instance."""
    print(f"Checking patch state for instance {instance_id}...")
    try:
        response = ssm.describe_instance_patch_states(
            InstanceIds=[instance_id]
        )
        
        if response['InstancePatchStates']:
            state = response['InstancePatchStates'][0]
            print(f"Missing Critical Patches: {state['MissingCount']}")
            print(f"Failed Patches: {state['FailedCount']}")
            print(f"Installed Patches: {state['InstalledCount']}")
            print(f"Last Operation: {state['Operation']}")
            print(f"Last Update Time: {state['LastUpdateTime']}")
            return state
        else:
            print("❓ No patch state information found")
            return None
    except Exception as e:
        print(f"❌ Error checking patch state: {e}")
        return None

def main():
    """Main function to orchestrate the test workflow."""
    args = parse_args()
    ssm, config, ec2, events, logs = init_clients(args.region)
    
    print("\n=== AUTOMATED PATCHING TEST SCRIPT ===")
    print(f"Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Testing instance: {args.instance_id}")
    print(f"AWS Region: {args.region}")
    print(f"Config Rule: {args.rule_name}")
    print("=====================================\n")
    
    # Step 1: Check if instance is managed by SSM
    if not check_instance_managed(ssm, args.instance_id):
        print("❌ Cannot proceed - instance is not managed by SSM")
        sys.exit(1)
    
    # Step 2: Check initial patch state
    print("\n=== INITIAL PATCH STATE ===")
    initial_state = check_patch_state(ssm, args.instance_id)
    if not initial_state:
        print("⚠️ Warning: Could not get initial patch state, but proceeding anyway")
    
    # Step 3: Create non-compliant state
    print("\n=== CREATING NON-COMPLIANT STATE ===")
    if not create_non_compliant_state(ssm, args.instance_id):
        print("❌ Failed to create non-compliant state")
        sys.exit(1)
    
    # Step 4: Force AWS Config evaluation
    print("\n=== FORCING CONFIG EVALUATION ===")
    if not force_config_evaluation(config, args.rule_name):
        print("❌ Failed to force AWS Config evaluation")
        sys.exit(1)
    
    # Step 5: Check for non-compliance
    print("\n=== WAITING FOR NON-COMPLIANCE DETECTION ===")
    print("This might take a few minutes...")
    compliant = True
    max_attempts = 5
    attempts = 0
    
    while compliant and attempts < max_attempts:
        time.sleep(60)  # Wait for a minute between checks
        attempts += 1
        print(f"Compliance check attempt {attempts}/{max_attempts}...")
        status = check_compliance_status(config, args.rule_name, args.instance_id)
        if status == 'NON_COMPLIANT':
            compliant = False
    
    if compliant:
        print("⚠️ Warning: Instance still showing as compliant after multiple checks")
        print("   You might need to wait longer or check Config settings")
    
    # Step 6: Look for automation execution
    print("\n=== CHECKING FOR AUTOMATION EXECUTION ===")
    print("Waiting for automation to start...")
    execution_id = None
    for i in range(5):  # Check every minute for 5 minutes
        execution_id = check_automation_execution(ssm, args.instance_id)
        if execution_id:
            break
        print(f"No automation found yet, checking again in 60 seconds (attempt {i+1}/5)...")
        time.sleep(60)
    
    # Step 7: Wait for automation to complete
    if execution_id:
        print("\n=== MONITORING AUTOMATION EXECUTION ===")
        final_status = wait_for_automation(ssm, execution_id, args.wait_time)
    else:
        print("⚠️ No automation execution was detected within the timeout period")
    
    # Step 8: Check final patch state
    print("\n=== FINAL PATCH STATE ===")
    final_state = check_patch_state(ssm, args.instance_id)
    
    # Step 9: Summary
    print("\n=== TEST SUMMARY ===")
    print(f"Instance ID: {args.instance_id}")
    print(f"Test Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if execution_id:
        print(f"Automation Executed: Yes (ID: {execution_id})")
        print(f"Automation Status: {final_status if final_status else 'Unknown'}")
    else:
        print("Automation Executed: No")
    
    if initial_state and final_state:
        initial_missing = initial_state['MissingCount']
        final_missing = final_state['MissingCount']
        print(f"Initial Missing Patches: {initial_missing}")
        print(f"Final Missing Patches: {final_missing}")
        
        if final_missing < initial_missing:
            print("✅ SUCCESS: Patches were installed by the automation")
        else:
            print("⚠️ WARNING: No reduction in missing patches detected")
    
    print("\nTest completed.")

if __name__ == "__main__":
    main()