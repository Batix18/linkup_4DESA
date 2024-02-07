# linkup_4DESA

install local
#create venv
py -m venv .venv
#active venv
Set-ExecutionPolicy Unrestricted -Scope Proces
.venv\Scripts\activate

#install librarie
pip install -r requirements.txt



```Bash 
az login 

#general
$location = 'westus3'
$resourceGroupName = 'ltestbois'
$storageAccountName = 'testboisstorage'
$contenaire='testbois'


$server='ltestboisserveurdb'
$logindb='superadmin'
$ServerDBpassword='/Password37'
$databaseName='inkupajbdb'
$sku="B_Gen5_1"
$startIp=0.0.0.0
$endIp=255.255.255.255

$appName="ltestboiswebapp"
$planName="testboisplan"
$gitrepo="https://github.com/Batix18/linkup_4DESA.git"

$superkeyapp="totototo"


az group create `
  --name $resourceGroupName `
  --location $location

az storage account create `
     --name $storageAccountName `
     --resource-group $resourceGroupName `
     --location $location `
     --sku 'Standard_LRS' `
     --kind 'StorageV2' `
     --allow-blob-public-access false

$response = az storage account show-connection-string -g $resourceGroupName -n $storageAccountName -o json
$connectionstring =  $response | ConvertFrom-Json

az storage container create --name $contenaire `
                            --account-name $storageAccountName `
                            --connection-string $connectionstring.connectionString

az postgres server create --name $server `
                          --resource-group $resourceGroupName `
                          --location $location `
                          --admin-user $logindb `
                          --admin-password $ServerDBpassword `
                          --sku-name $sku

az postgres server firewall-rule create --resource-group $resourceGroupName `
                                        --server $server `
                                        --name AllowIps `
                                        --start-ip-address $startIp `
                                        --end-ip-address $endIp 

az postgres db create -g $resourceGroup `
                      -s $server `
                      -n $databaseName

az appservice plan create `
    -n $planName `
    -g $resourceGroupName `
    -l $location `
    --is-linux `
    --sku B1

az webapp create `
    -n $appName `
    -g $resourceGroupName `
    --plan $planName `
    --runtime "PYTHON:3.11"
    

az webapp deployment source config `
    -n $appName `
    -g $resourceGroupName `
    --repo-url $gitrepo `
    --branch main `
    --manual-integration

az webapp config set `
    --resource-group $resourceGroupName `
    --name $appName `
    --startup-file "gunicorn --bind=0.0.0.0 --timeout 600 main:app"

az webapp config appsettings set `
    --resource-group $resourceGroupName `
    --name $appName `
    --settings AZURE_SQL_HOST="$($server).postgres.database.azure.com"

az webapp config appsettings set `
    --resource-group $resourceGroupName `
    --name $appName `
    --settings AZURE_SQL_DB=$databaseName

az webapp config appsettings set `
    --resource-group $resourceGroupName `
    --name $appName `
    --settings AZURE_SQL_USER=$logindb

az webapp config appsettings set `
    --resource-group $resourceGroupName `
    --name $appName `
    --settings AZURE_SQL_PASSWORD=$ServerDBpassword

az webapp config appsettings set `
    --resource-group $resourceGroupName `
    --name $appName `
    --settings APP_SUPER_KEY=$superkeyapp

az webapp config appsettings set `
    --resource-group $resourceGroupName `
    --name $appName `
    --settings AZURE_CONNECTION_STORAGE=$connectionstring