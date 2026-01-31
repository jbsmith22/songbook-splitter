# Subscribe to SNS alerts
# Replace YOUR_EMAIL with your actual email address

$EMAIL = Read-Host "Enter your email address for alerts"

aws sns subscribe `
    --topic-arn "arn:aws:sns:us-east-1:227027150061:jsmith-sheetmusic-splitter-alarms" `
    --protocol email `
    --notification-endpoint $EMAIL `
    --region us-east-1

Write-Host ""
Write-Host "Subscription request sent!" -ForegroundColor Green
Write-Host "Check your email and confirm the subscription." -ForegroundColor Yellow
