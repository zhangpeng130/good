#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FUNCTIONS=(send_code verify_login trigger_sos heartbeat check_risk)
BUILD_DIR="${ROOT_DIR}/dist/functions"
TEMP_DIR="${ROOT_DIR}/.tmp/function_build"
REQ_FILE="${ROOT_DIR}/cloudfunctions/requirements.txt"

RUN_TERRAFORM="${RUN_TERRAFORM:-0}"
TENCENT_REGION="${TENCENT_REGION:-ap-guangzhou}"
COS_BUCKET="${COS_BUCKET:-}"
COS_PREFIX="${COS_PREFIX:-functions}"
SCF_NAMESPACE="${SCF_NAMESPACE:-good-prod}"
FUNCTION_NAME_PREFIX="${FUNCTION_NAME_PREFIX:-${SCF_NAMESPACE}}"

echo "[1/4] Packaging SCF functions..."
rm -rf "${BUILD_DIR}" "${TEMP_DIR}"
mkdir -p "${BUILD_DIR}" "${TEMP_DIR}"

for fn in "${FUNCTIONS[@]}"; do
  stage_dir="${TEMP_DIR}/${fn}"
  mkdir -p "${stage_dir}"
  python3 -m pip install --upgrade -r "${REQ_FILE}" -t "${stage_dir}" >/dev/null
  cp "${ROOT_DIR}/cloudfunctions/${fn}/main.py" "${stage_dir}/main.py"
  cp -r "${ROOT_DIR}/cloudfunctions/common" "${stage_dir}/common"
  (
    cd "${stage_dir}"
    zip -qr "${BUILD_DIR}/${fn}.zip" .
  )
  echo "  - ${fn}.zip ready"
done

if [[ "${RUN_TERRAFORM}" == "1" ]]; then
  echo "[2/4] Applying Terraform infrastructure..."
  terraform -chdir="${ROOT_DIR}/infra" init
  terraform -chdir="${ROOT_DIR}/infra" apply -auto-approve
else
  echo "[2/4] Skip terraform apply (set RUN_TERRAFORM=1 to enable)."
fi

if [[ -z "${COS_BUCKET}" ]]; then
  echo "COS_BUCKET is empty. Only package build done."
  exit 0
fi

echo "[3/4] Uploading ZIP packages to COS bucket ${COS_BUCKET}..."
for fn in "${FUNCTIONS[@]}"; do
  tccli cos cp "${BUILD_DIR}/${fn}.zip" "cos://${COS_BUCKET}/${COS_PREFIX}/${fn}.zip"
done

echo "[4/4] Updating SCF function code..."
for fn in "${FUNCTIONS[@]}"; do
  function_name="${FUNCTION_NAME_PREFIX}-${fn}"
  tccli scf UpdateFunctionCode \
    --FunctionName "${function_name}" \
    --Namespace "${SCF_NAMESPACE}" \
    --CosBucketName "${COS_BUCKET}" \
    --CosBucketRegion "${TENCENT_REGION}" \
    --CosObjectName "${COS_PREFIX}/${fn}.zip" >/dev/null
  echo "  - ${function_name} updated"
done

echo "Deploy completed."

