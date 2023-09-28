## Deployment

If there are database changes involved, update cronjob-configmap-default.yaml and cronjob-configmap-dev.yaml to use a newer database version. E.g. if it's previously using `schedulerdb_202315_dev__v4`, update it to `schedulerdb_202315_dev__v5`. Then, make sure the `grafana_readonly` account has the necessary permissions by running the following commands inside the database server once the job has run:

```
GRANT SELECT ON ALL TABLES IN SCHEMA public TO grafana_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO grafana_readonly;
```

And then update the data source (and dashboard if necessary) in Grafana.
