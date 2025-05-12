# Testing Shield Advanced's Layer 7 Auto mitigation

## Protect a resource using Shield Advanced

Create a resource in AWS (e.g. CloudFront distribution), protect it with Shield Advanced (L7AM enabled in block), and configure the appropriate health checks that fail during the DDoS attack to make Shield Advanced detection more sensitive. 

## Deploy the baselining tool

To test the automatic DDoS protection of Shield Advance at layer 7, first create a baseline of normal traffic. Shield Advanced detects DDoS events when there is a significant deviatation from the normal baseline traffic. Run the following command to create the baselining tool, after changeing the S3 bucket name to a bucket you own:

```
git clone https://github.com/achrafsouk/l7am-testing.git
cd l7am-testing
aws cloudformation package --template-file template.yaml --s3-bucket "YOUR_BUCKET_NAME" --s3-prefix "l7am-testing" --output-template-file template-processed.yaml
aws cloudformation deploy --template-file template-processed.yaml --stack-name "shield-testing-l7am" --capabilities CAPABILITY_IAM
```

## Generate normal traffic baseline

The stack created a Amazon DynamoDB table named **%L7AMBaselineResources%**. To start generating baseline traffic, create an item in the table with the following format, using your created :

{
 "hostname": "YOUR_PORTECTED_RESOURCE.COM",
 "max_requests_per_min": 2000,
 "min_requests_per_min": 5,
 "parallelism": 10,
 "protocol": "https"
}

> [!WARNING]
> Leave the baselining tool running for at least 48 hours before starting the test.

<img width="488" alt="image" src="https://github.com/user-attachments/assets/04060340-2662-400d-8dba-2fb708014cb3" />


## Simulate a DDoS attack

After waiting for 48 hours, simulate an attack using ddosify (https://github.com/ddosify/ddosify). First, Go to AWS CloudShell and install the tool:

```
sudo yum -y install golang
go install go.ddosify.com/ddosify@latest
```
Then start an attack (e.g. 1K RPS for 20 mins) using the below command after changeing the target url to your protected resource 

```
~/go/bin/ddosify -n 1200000 -d 1200 -h "User-Agent: DemoAttack" -t https://YOUR_PORTECTED_RESOURCE.COM/PATH -l waved
```

Verify how the attack is mitigated using WAF metrics, and in the Shield Advance console.

