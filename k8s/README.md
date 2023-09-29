## Deployment

If there are database changes involved, update cronjob-configmap-default.yaml and cronjob-configmap-dev.yaml to use a newer database version. E.g. if it's previously using `schedulerdb_202315_dev__v4`, update it to `schedulerdb_202315_dev__v5`.

<!-- Then, make sure the `grafana_readonly` account has the necessary permissions by running the following commands inside the database server once the job has run:

```
GRANT SELECT ON ALL TABLES IN SCHEMA public TO grafana_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO grafana_readonly;
``` -->

And then update the data source (and dashboard if necessary) in Grafana.

## Useful links

Accessing PVC: https://stackoverflow.com/a/70323207

## Useful commands

#### Accessing performance file

```
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
name: pvc-inspector
spec:
containers:

- image: busybox
  name: pvc-inspector
  command: ["tail"]
  args: ["-f", "/dev/null"]
  volumeMounts:
  - mountPath: /pvc
    name: pvc-mount
    volumes:
- name: pvc-mount
  persistentVolumeClaim:
  claimName: drexel-scheduler-performance-pvc
  EOF
```

```
kubectl cp dev/pvc-inspector:pvc/profile_output.pstat ./performance/profile_output.pstat
pyprof2calltree -i performance/profile_output.pstat -o performance/callgrind.out.profile
qcachegrind performance/callgrind.out.profile
python3 performance/analyze.py
kubectl delete pod pvc-inspector
```
