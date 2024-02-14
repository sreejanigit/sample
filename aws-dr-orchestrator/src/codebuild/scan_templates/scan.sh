
# Scan the DR orchestrator templates
echo "Scanning: dr-orchestrator templates"
for path in src/dr-orchestrator/*; do
  if [ -d "$path" ]; then
    dir=$(basename "$path")
    echo "Scanning: ${dir}"
    cfn_nag $path/*.y* --blacklist-path src/codebuild/scan_templates/exceptions.yaml;
  fi
done