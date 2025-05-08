## CloudWatch Logs Configuration

The CloudFormation template automatically creates the following CloudWatch Logs resources:

1. **SSM Automation Log Group**:
   - Log group name: `/aws/ssm/automation/[StackName]`
   - Retention period: 30 days
   - Used to store detailed logs from SSM Automation executions

2. **Lambda Function Log Group**:
   - Automatically created by AWS Lambda
   - Contains logs from the PatchLogger function
   - Shows event details each time a non-compliant instance is detected

To view logs after deployment:

1. Navigate to CloudWatch > Log Groups
2. Search for either:
   - `/aws/ssm/automation/[StackName]` - for SSM Automation logs
   - `/aws/lambda/PatchLogger` - for Lambda function logs

These logs are valuable for troubleshooting issues and auditing patch operations.## Patch Baseline Configuration

The CloudFormation template sets up a default patch baseline for Amazon Linux 2 instances that includes:

1. **Patch Criteria**:
   - Security patches (Critical and Important severity)
   - Bugfix patches
   - Approval after 7 days of release

2. **Patch Group**:
   - The EC2 instance is tagged with the "DefaultPatchGroup" patch group
   - The patch baseline is associated with this patch group

If you want to customize the patch baseline after deployment:

1. Navigate to AWS Systems Manager > Patch Manager
2. Select the created patch baseline (DefaultServerPatchBaseline)
3. Click "Modify" to adjust patch approval rules
4. Save your changes

You can also create additional patch groups and associate them with different patch baselines for more granular control.## Prerequisites

1. An AWS account with administrator access
2. AWS CLI installed and configured with appropriate credentials
3. An existing EC2 key pair for SSH access
4. A valid email address to receive patch notifications# Automated Patching Lab - Setup Instructions

This document provides instructions for deploying and testing the Automated Patching solution using the CloudFormation template.

## Network Requirements

The EC2 instance must be able to communicate with the AWS Systems Manager service endpoints. You can meet this requirement through:

1. **Public Subnet with Internet Access**: The instance needs a route to the internet (via an Internet Gateway) and a public IP
2. **VPC Endpoints for SSM Services**: If using a private subnet, you'll need the following endpoints:
   - com.amazonaws.[region].ssm
   - com.amazonaws.[region].ec2messages
   - com.amazonaws.[region].ssmmessages
   - (Optional) com.amazonaws.[region].s3 if using Amazon S3 for SSM artifacts

The CloudFormation template by default creates a VPC with public subnet and internet access, so no additional VPC endpoints are required.

## Deployment Steps

1. **Deploy the CloudFormation Stack**

   ```bash
   aws cloudformation create-stack \
     --stack-name AutomatedPatchingLab \
     --template-body file://automated-patching-template.yaml \
     --parameters \
       ParameterKey=KeyName,ParameterValue=YOUR_KEY_PAIR_NAME \
       ParameterKey=EmailAddress,ParameterValue=YOUR_EMAIL_ADDRESS \
     --capabilities CAPABILITY_IAM
   ```

   Replace `YOUR_KEY_PAIR_NAME` with your existing EC2 key pair name and `YOUR_EMAIL_ADDRESS` with your email address.

2. **Monitor Stack Creation**

   ```bash
   aws cloudformation describe-stacks \
     --stack-name AutomatedPatchingLab \
     --query "Stacks[0].StackStatus"
   ```

3. **Confirm SNS Subscription**

   Check your email for a subscription confirmation message from AWS and click the confirmation link.

## Testing the Automated Patching

1. **Verify AWS Config Setup**

   Navigate to the AWS Config console and verify that:
   - The configuration recorder is active
   - The patch compliance rule is present

2. **Verify SSM Connection**

   Navigate to the AWS Systems Manager console > Fleet Manager and confirm your EC2 instance appears as "Managed".

3. **Simulate Patch Non-Compliance**

   SSH into your EC2 instance:

   ```bash
   ssh -i YOUR_KEY_PAIR.pem ec2-user@INSTANCE_PUBLIC_IP
   ```

   Modify the update configuration:

   ```bash
   sudo sed -i 's/repo_upgrade: security/repo_upgrade: none/' /etc/cloud/cloud.cfg
   ```

   Or use Systems Manager to scan for missing patches:

   ```bash
   aws ssm send-command \
     --document-name "AWS-RunPatchBaseline" \
     --targets "Key=instanceids,Values=INSTANCE_ID" \
     --parameters "Operation=Scan" \
     --region YOUR_REGION
   ```

4. **Force AWS Config Evaluation**

   ```bash
   aws configservice start-config-rules-evaluation \
     --config-rule-names ec2-managedinstance-patch-compliance-status-check
   ```

5. **Monitor the Results**

   - Check the AWS Config console to see if your instance becomes non-compliant
   - Watch for an email notification about patch automation
   - Check AWS Systems Manager > Automation to see the patching operation
   - Review CloudWatch Logs for the Lambda function logs

## Troubleshooting

### AWS Config Not Detecting Non-Compliance
- Verify that the SSM Agent is running: `sudo systemctl status amazon-ssm-agent`
- Check that the instance has the correct IAM role attached
- Manually scan for patches to verify non-compliance

### Automation Not Triggered
- Check EventBridge rule configuration 
- Verify that the SSM Automation role has proper permissions
- Check CloudWatch logs for any errors

### Patching Not Successful
- Check that the instance has internet connectivity to download patches
- Verify SSM Automation execution details for error messages
- Ensure the instance has enough disk space for updates

## Cleanup

To delete all resources created by this lab:

```bash
aws cloudformation delete-stack --stack-name AutomatedPatchingLab
```

## Architecture Diagram

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│   AWS Config    │────▶│  EventBridge    │────▶│    SSM          │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         │ Patch
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │                 │
                                                │  EC2 Instance   │
                                                │                 │
                                                └─────────────────┘
                                                         │
                                                         │ Notification
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │                 │
                                                │  Amazon SNS     │──▶ Email
                                                │                 │
                                                └─────────────────┘
                                                         │
                                                         │ Log
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │                 │
                                                │  Lambda         │
                                                │                 │
                                                └─────────────────┘
```