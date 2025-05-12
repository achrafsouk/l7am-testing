# Testing Shield Advanced's Layer 7 Auto mitigation



## Create normal baseline

To test the automatic DDoS protection of Shield Advance at layer 7, first create a baseline of normal traffic. Shield Advanced detects DDoS events when there is a significant deviatation from the normal baseline traffic. Run the following command to start baselining, after changeing the S3 bucket name to a bucket you own:

```
git clone https://github.com/achrafsouk/l7am-testing.git
cd l7am-testing
aws cloudformation package --template-file template.yaml --s3-bucket "YOUR_BUCKET_NAME" --s3-prefix "l7am-testing" --output-template-file template-processed.yaml
aws cloudformation deploy --template-file template-processed.yaml --stack-name "shield-testing-l7am" --capabilities CAPABILITY_IAM
```

## Protect a resource using Shield Advanced

Create a resource in AWS (e.g. CloudFront distribution), protect it with Shield Advanced, and configure the appropriate health checks. To succeed the test:
- Configure health checks that fail during your test. Failed health checks, will enable Shield Advanced to detect DDoS attacks with higher sensitivity.
- Make sure you configure L7AM with block action.
- Leave the baselining tool running for at least 48 hours.

<img width="488" alt="image" src="https://github.com/user-attachments/assets/04060340-2662-400d-8dba-2fb708014cb3" />

## Start a DDoS attack

To simulate an attack you can use ddosify (https://github.com/ddosify/ddosify):

Go to AWS CloudShell and install the tool:
```
sudo yum -y install golang
go install go.ddosify.com/ddosify@latest
```
Then start an attack (e.g. 1K RPS for 20 mins) using the below command after changeing the target url to your protected resource 

```
~/go/bin/ddosify -n 1200000 -d 1200 -h "User-Agent: DemoAttack" -t https://YOUR_PORTECTED_RESOURCE.COM/PATH -l waved
```

Verify how the attack is mitigated using WAF metrics.

