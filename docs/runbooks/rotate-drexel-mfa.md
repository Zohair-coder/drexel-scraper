# Rotate Drexel MFA Credentials

Use this runbook when the scraper reports that Microsoft requires the Drexel
account to update its security information.

## 1. Register A New Authenticator

1. Open [Microsoft Security info](https://mysignins.microsoft.com/security-info)
   and sign in with the scraper's Drexel account.
2. Complete any security-information prompt.
3. Select **Add sign-in method**.
4. Select **Microsoft Authenticator**, then select
   **I want to use a different authenticator app**.
5. Continue until the QR code appears, then select **Can't scan image?**.
6. Keep the displayed secret key available. Do not close the Microsoft page.

## 2. Verify And Store The Secret

From the repository root, activate the virtual environment and read the new
secret without placing it in shell history:

```zsh
source .venv/bin/activate
read -rs "NEW_DREXEL_MFA_SECRET_KEY?New Drexel MFA secret key: "
printf '\n'
export NEW_DREXEL_MFA_SECRET_KEY
DREXEL_MFA_SECRET_KEY="$NEW_DREXEL_MFA_SECRET_KEY" python src/totp.py
```

Enter the generated code on Microsoft's website and finish the registration.
Then update the existing `DREXEL_MFA_SECRET_KEY` assignment in `~/.zshenv`:

```zsh
${EDITOR:-vi} ~/.zshenv
source ~/.zshenv
```

Verify that all required variables are loaded without printing their values:

```zsh
[[ -n "$DREXEL_EMAIL" && -n "$DREXEL_PASSWORD" && -n "$DREXEL_MFA_SECRET_KEY" ]] \
  && print "Drexel credentials are set" \
  || print "A Drexel credential is missing"
```

Run the scraper locally:

```zsh
python src/main.py
```

Do not continue until the scraper passes Microsoft authentication.

## 3. Update Kubernetes

Confirm that `kubectl` is using the intended cluster:

```zsh
kubectl config current-context
```

Update the complete credential Secret in production and development. Recreating
the manifest with all three keys prevents `kubectl apply` from removing an
existing credential:

```zsh
for namespace in default dev; do
  kubectl create secret generic drexel-scheduler-secrets \
    --namespace "$namespace" \
    --from-literal="DREXEL_EMAIL=$DREXEL_EMAIL" \
    --from-literal="DREXEL_PASSWORD=$DREXEL_PASSWORD" \
    --from-literal="DREXEL_MFA_SECRET_KEY=$DREXEL_MFA_SECRET_KEY" \
    --dry-run=client \
    --output=yaml \
    | kubectl apply --namespace "$namespace" -f -
done
```

The CronJob reads the Secret when each Pod starts, so existing Pods will not
receive the new value.

## 4. Verify The CronJob

Run and inspect a one-off production Job:

```zsh
namespace=default
job="drexel-scheduler-mfa-check-$(date +%s)"
kubectl create job "$job" \
  --namespace "$namespace" \
  --from=cronjob/drexel-scheduler-cronjob
kubectl logs --namespace "$namespace" --follow "job/$job"
kubectl get job --namespace "$namespace" "$job"
```

To verify development instead, set `namespace=dev` before creating the Job.
Delete the one-off Job after verification:

```zsh
kubectl delete job --namespace "$namespace" "$job"
```

Finally, remove the temporary shell variable:

```zsh
unset NEW_DREXEL_MFA_SECRET_KEY
```
