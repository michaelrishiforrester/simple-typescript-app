### Verifying Automation Completion and Patching Success

After automation completes, you can verify the patching success with these steps:

1. **Check if the instance is now compliant**:
   ```bash
   # Force a re-evaluation of the Config rule
   aws configservice start-config-rules-evaluation \
     --config-rule-names ec2-managedinstance-patch-compliance-status-check
   
   # Wait a minute or two, then check the compliance status
   aws configservice get-compliance-details-by-resource \
     --resource-type AWS::EC2::Instance \
     --resource-id i-0123456789abcdef0
   ```

2. **Verify no missing patches remain**:
   ```bash
   aws ssm describe-instance-patch-states \
     --instance-ids i-0123456789abcdef0
   ```

3. **Get detailed patch log**:
   ```bash
   aws ssm describe-instance-patches \
     --instance-id i-0123456789abcdef0 \
     --filters Key=State,Values=Installed
   ```

These steps help confirm that the automation completed successfully and actually resolved the patch compliance issue.### Validating Patch Baseline Association

**Symptoms:** No patches are applied or non-compliance isn't detected

**Solution:**
1. Verify the patch baseline is correctly associated:
   ```bash
   aws ssm describe-patch-groups --region us-east-1
   ```

2. Verify the instance is properly tagged with the correct patch group:
   ```bash
   aws ec2 describe-tags --filters "Name=resource-id,Values=i-0123456789abcdef0" "Name=key,Values=PatchGroup"
   ```

3. Check if the default patch baseline is being used:
   ```bash
   aws ssm get-default-patch-baseline --region us-east-1
   ```

4. If using a custom patch baseline, verify it includes the right operating system:
   ```bash
   aws ssm describe-patch-baselines --filters "Key=NAME_PREFIX,Values=DefaultServer"
   ```# Troubleshooting and Testing Guide

This guide provides detailed steps for debugging common issues and testing the automated patching solution.

## Simulating Patch Non-Compliance

There are several ways to create a non-compliant state to test the automation:

### Method 1: Modify Cloud-Init Configuration

```bash
sudo sed -i 's/repo_upgrade: security/repo_upgrade: none/' /etc/cloud/cloud.cfg
```

This modifies the cloud-init configuration to prevent automatic security updates.

### Method 2: Force a Patch Scan

Run a scan operation which will identify missing patches but not install them:

```bash
aws ssm send-command \
  --document-name "AWS-RunPatchBaseline" \
  --targets "Key=instanceids,Values=i-0123456789abcdef0" \
  --parameters "Operation=Scan" \
  --region us-east-1
```

Replace the instance ID and region with your actual values.

### Method 3: Change Patch Baseline

For a more controlled test, you can create a custom patch baseline with more strict requirements:

1. Go to AWS Systems Manager > Patch Manager
2. Create a custom patch baseline
3. Set a more aggressive patching rule (e.g., include all patches not just security)
4. Associate it with your instance

## Verifying Component Status

### AWS Config

Check if AWS Config is properly recording the instance:

```bash
aws configservice describe-configuration-recorders
aws configservice describe-configuration-recorder-status
```

Force an immediate evaluation:

```bash
aws configservice start-config-rules-evaluation \
  --config-rule-names ec2-managedinstance-patch-compliance-status-check
```

Check the rule compliance status:

```bash
aws configservice describe-compliance-by-config-rule \
  --config-rule-names ec2-managedinstance-patch-compliance-status-check
```

### EventBridge Rule

Verify EventBridge rule configuration:

```bash
aws events describe-rule --name PatchDriftCatcher
```

Check rule targets:

```bash
aws events list-targets-by-rule --rule PatchDriftCatcher
```

### Systems Manager

Check if the instance is properly managed by Systems Manager:

```bash
aws ssm describe-instance-information
```

Verify patch compliance state:

```bash
aws ssm describe-instance-patch-states \
  --instance-ids i-0123456789abcdef0
```

Get detailed patch information:

```bash
aws ssm describe-instance-patches \
  --instance-id i-0123456789abcdef0
```

### SNS Topic

List subscriptions to ensure email is properly subscribed:

```bash
aws sns list-subscriptions-by-topic --topic-arn TOPIC_ARN
```

Manually publish a test message:

```bash
aws sns publish \
  --topic-arn TOPIC_ARN \
  --message "This is a test message for the patch automation system"
```

### Lambda Logging

Check Lambda execution logs:

```bash
aws logs describe-log-streams \
  --log-group-name /aws/lambda/PatchLogger
```

View specific log events:

```bash
aws logs get-log-events \
  --log-group-name /aws/lambda/PatchLogger \
  --log-stream-name STREAM_NAME
```

## Common Issues and Solutions

### SSM Agent Not Running

**Symptoms:** Instance doesn't appear in Systems Manager, patch compliance unknown

**Solution:**
```bash
sudo systemctl status amazon-ssm-agent
sudo systemctl start amazon-ssm-agent
```

### Permission Issues

**Symptoms:** Automation fails, access denied errors in logs

**Solution:** Check IAM role permissions for:
- EC2 instance role (SSM access, including `ec2messages:*`, `ssmmessages:*`, and `ssm:DescribeInstanceInformation`)
- EventBridge role (SSM Automation execution and `iam:PassRole`)
- Config role (S3 bucket access)
- SSM Automation role (appropriate EC2 and SSM permissions)

### Network Connectivity Issues

**Symptoms:** Patching fails, timeouts in SSM execution

**Solution:**
1. Verify Security Group allows outbound traffic to download patches
2. Check VPC endpoints or NAT gateway configuration if applicable
3. Test connectivity from the instance:
   ```bash
   ping amazon.com
   curl -I https://amazonlinux.us-east-1.amazonaws.com
   ```

### EventBridge Rule Not Triggering

**Symptoms:** Non-compliance detected but no automation starts

**Solution:**
1. Verify rule pattern matches the actual events
2. Check that the input transformation template is correctly formatted
3. Ensure the EventBridge role has `iam:PassRole` permission for the SSM Automation role
4. Enable CloudWatch Logs for the rule
5. Test with a manual event:
   ```bash
   aws events put-events --entries file://test-event.json
   ```

The `test-event.json` file could contain:
```json
{
  "Source": "aws.config",
  "DetailType": "Config Rules Compliance Change",
  "Detail": "{\"configRuleName\":\"ec2-managedinstance-patch-compliance-status-check\",\"resourceId\":\"i-0123456789abcdef0\",\"resourceType\":\"AWS::EC2::Instance\",\"newEvaluationResult\":{\"complianceType\":\"NON_COMPLIANT\"}}",
  "Resources": []
}
```

## Advanced Testing Techniques

### Monitoring EventBridge Events in Real-Time

Create a temporary CloudWatch Logs destination for EventBridge events:

```bash
aws events put-rule \
  --name DebugAllEvents \
  --event-pattern "{}"

aws events put-targets \
  --rule DebugAllEvents \
  --targets "Id"="1","Arn"="LAMBDA_ARN"
```

Create a simple Lambda function that logs all incoming events.

### Testing SSM Automation Document Directly

Run the patch baseline directly to verify it works:

```bash
aws ssm start-automation-execution \
  --document-name AWS-RunPatchBaseline \
  --parameters "InstanceIds=i-0123456789abcdef0,Operation=Install" \
  --automation-execution-role SSM_AUTOMATION_ROLE_ARN
```

### Simulating Complete System Flow

1. Run an instance patch state check
2. Mark the instance as non-compliant in Config (may require manual adjustment)
3. Trace the event flow through EventBridge
4. Monitor SSM Automation execution
5. Verify notification delivery
6. Check final patch compliance state

## Cleanup After Testing

To clean up test resources:

```bash
# Stop any running automations
aws ssm stop-automation-execution --automation-execution-id EXECUTION_ID

# Delete temporary test rules
aws events remove-targets --rule DebugAllEvents --ids 1
aws events delete-rule --name DebugAllEvents

# Return the instance to a clean state
aws ssm send-command \
  --document-name "AWS-RunPatchBaseline" \
  --targets "Key=instanceids,Values=i-0123456789abcdef0" \
  --parameters "Operation=Install,RebootOption=RebootIfNeeded"
```