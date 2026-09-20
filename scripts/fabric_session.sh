#!/usr/bin/env bash

export AZURE_CONFIG_DIR="$HOME/.azure-fabric"

export FABRIC_TENANT_ID="bb9d40a1-e979-48ca-968a-37abf10e1717"
export WORKSPACE_ID="81e75ca0-f556-48c0-9dea-4851ce7bf916"

export BRONZE_ID="b9a4e5f8-5c7f-41b5-bd54-7241fed3dc12"
export SILVER_ID="d4a65e02-93bd-4109-9acc-80c8c57e6b4d"
export GOLD_ID="ce6454df-212a-438a-809d-7f77075fb5c9"

export DFE_PIPELINE_ID="d74cac73-5175-47e6-b3e1-f36bb54e5c3d"
export NOMIS_PIPELINE_ID="9d8cf3d5-3430-4bb0-8814-a8e5cd8ada1f"

export B2S_NOTEBOOK_ID="91fb3609-26ce-4bb5-9332-f282a1349614"
export SILVER_MODEL_NOTEBOOK_ID="2ab72583-94c5-4853-8867-c386e85d5e29"
export B2S_PIPELINE_ID="e446f1f5-a03c-462e-aada-0dfe5bc21903"

export ONELAKE_DFS="https://southafricanorth-onelake.dfs.fabric.microsoft.com"
export ONELAKE_BLOB="https://southafricanorth-onelake.blob.fabric.microsoft.com"

if ! az account show >/dev/null 2>&1; then
    echo "Fabric Azure CLI session is not authenticated."
    echo "Run:"
    echo "az login --use-device-code --allow-no-subscriptions"
    return 1 2>/dev/null || exit 1
fi

export FABRIC_TOKEN=$(az account get-access-token     --resource https://api.fabric.microsoft.com     --query accessToken -o tsv)

export ONELAKE_TOKEN=$(az account get-access-token     --resource https://storage.azure.com/     --query accessToken -o tsv)

echo "Fabric session ready."
echo "Workspace: GM SkillsFlow Dev"
echo "Workspace ID: $WORKSPACE_ID"

export SILVER_MODEL_PIPELINE_ID="9ab81518-0410-4bfc-bf80-ad031df6a5f3"

export SILVER_TO_GOLD_NOTEBOOK_ID="8acb2ede-0045-4859-9d1c-13a3f5c87917"

export SILVER_TO_GOLD_PIPELINE_ID="304cee55-294a-4999-9410-b6a0e6c5f809"
