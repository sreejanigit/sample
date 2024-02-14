# deploy the baseline resources
echo "INFO: Deploying stacks in $2 region($1)"
echo "INFO: Deploying baseline resources... "
aws cloudformation deploy --template-file baseline.yaml --stack-name dr-orchestrator-baseline --capabilities CAPABILITY_NAMED_IAM --region $2

# deploy the baseline resources
if [ $1=='primary']; then
    echo "INFO: Deploying IAM roles... "
    aws cloudformation deploy --template-file baseline-iamroles.yaml --stack-name dr-orchestrator-cicd-roles --capabilities CAPABILITY_NAMED_IAM --region $2
fi

# Zip the project files ignoring the .git
echo "INFO: Zipping project files... "
pushd .
cd ../..
zip -rq dr-orchestrator.zip . -x .git/\* .DS_Store 
# upload to S3 bucket created in the baseline template
bucket_name=$(aws cloudformation list-exports --query 'Exports[?Name==`dr-orchestrator-s3-name`].Value' --output text --region $2)

echo "INFO: Uploading to S3 bucket $bucket_name..."
aws s3 cp dr-orchestrator.zip "s3://$bucket_name/dr-orchestrator.zip" --region $2
rm dr-orchestrator.zip
popd

# Deploy the codecommit repo
echo "INFO: Deploying codecommit repo..."
aws cloudformation deploy --template-file codecommit.yaml --stack-name dr-orchestrator-repository --capabilities CAPABILITY_NAMED_IAM --region $2

# Deploy the codecommit repo
echo "INFO: Deploying codebuild stages..."
aws cloudformation deploy --template-file codebuild.yaml --stack-name dr-orchestrator-build-stages --capabilities CAPABILITY_NAMED_IAM --region $2

# Deploy the codecommit repo
echo "INFO: Deploying codepipeline..."
aws cloudformation deploy --template-file ../../pipeline.yaml --stack-name dr-orchestrator-pipeline --capabilities CAPABILITY_NAMED_IAM --region $2

echo "INFO: Done!"

