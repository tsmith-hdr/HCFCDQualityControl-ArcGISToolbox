# Common Issues
## AGOL Authentication
### Error: Tool is not Licensed
A number of the Tools have logic in the <i>isLicensed</i> method to check that the active portal URL matches the HCFCD SAFER PDS URL. If you receive this error, check the active portal and if the logged in account has the appropriate privileges.

Another issue could be that the PORTAL_URL constant is not set to the correct URL. This variable is stored in src/constants/paths.py. 