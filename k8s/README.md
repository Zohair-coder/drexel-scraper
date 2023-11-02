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

#### Accessing database locally

```
kubectl port-forward service/postgres-postgresql 5432:5432 -n postgres
```
