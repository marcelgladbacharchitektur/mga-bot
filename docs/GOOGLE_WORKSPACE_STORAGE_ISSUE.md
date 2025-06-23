# Google Workspace Storage Limit Issue

## Problem Summary
- **Expected**: 5 TB (Business Plus Plan)
- **Actual**: 300 GB shown in Drive
- **Impact**: 94% less storage than paid for

## Diagnostic Steps

### 1. Admin Console Check
Navigate to: https://admin.google.com
- Go to: Storage (or Reports → Storage)
- Check: Total storage limit for organization
- Screenshot the storage page

### 2. Billing Verification
Navigate to: https://admin.google.com/billing
- Verify active subscription shows "Business Plus"
- Check billing history
- Note subscription start date

### 3. User License Check
Navigate to: Users → Select your user
- Check assigned licenses
- Verify "Business Plus" is assigned

## Possible Causes

### A. Legacy Plan Migration Issue
- Old G Suite Business (300GB limit)
- Not properly migrated to new Business Plus

### B. Provisioning Error
- Subscription active but resources not allocated
- Common with new accounts

### C. Trial vs Paid Status
- Trial accounts may have different limits
- Payment processing delays

## Resolution Path

### Immediate Actions:
1. Document current storage status (screenshots)
2. Check exact plan name in Admin Console
3. Contact Google Workspace Support

### Support Script:
"I have a Business Plus subscription but my storage shows only 300GB instead of 5TB. My admin console shows [PLAN NAME]. Please provision the correct 5TB storage pool for my Business Plus account."

## Contact Information
- Google Workspace Support: https://support.google.com/a/contact/admin_support
- Phone: Available in Admin Console
- Chat: Available during business hours

## Expected Resolution
- Storage should be updated to 5TB within 24-48 hours
- No data migration needed
- Retroactive from subscription start