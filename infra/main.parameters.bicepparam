using './main.bicep'

param environment = 'prod'
param location = 'westus'
param sqlAdminLogin = 'ltbla-admin'
param sqlAdminPassword = ''      // Set at deploy time: azd up --parameter sqlAdminPassword=<value>
param anthropicApiKey = ''       // Set at deploy time or via az keyvault secret set
param graphTenantId = ''         // Your Azure AD tenant ID
param graphClientId = ''         // App registration client ID
param graphClientSecret = ''     // App registration client secret
