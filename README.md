Beam Flink & Kubernetes
---

This repo is a bare minimum sample of running a python beam pipeline on flink deployed in a kubernetes cluster.

Setup (via minikube)
-----

This assumes you're starting in an environment with python, a recent version of beam installed, and [minikube](https://kubernetes.io/docs/tasks/tools/install-minikube/). 

Start up a simple minikube k8s cluster
```shell script
minikube start --cpus 4 --memory=6144 --disk-size='20gb'
```

Build a slightly modified flink image that has docker installed. Building this directly in the minikube registry simplifies things.
```shell script
eval $(minikube docker-env)
docker build ./flink -t docker-flink:1.10
```

Deploy the flink components to kubernetes.
```shell script
kubectl apply -f ./k8s/flink.yaml
```

Wait a minute for the pods to spin up.
```shell script
kubectl get pods
```

[Recommended] Pre-download the sdk container in the docker-in-docker service on the taskworker. If you don't do this then the taskworker may timeout waiting for the sdk container to spin up.
```shell script
PYTHON_VERSION=$(python --version | cut -d" " -f2 | cut -d"." -f1-2)
BEAM_VERSION=$(python -c "import apache_beam;print(apache_beam.__version__)")
TASKMANAGER_POD=$(kubectl get pods --selector=component=taskmanager --no-headers -o name)
kubectl exec ${TASKMANAGER_POD} -c taskmanager -- docker pull apache/beam_python${PYTHON_VERSION}_sdk:${BEAM_VERSION}
```

Submit a beam pipeline.
```shell script
FLINK_MASTER_URL=$(minikube service flink-jobmanager-rest --url)
python -m pipeline --runner=FlinkRunner --flink_version 1.10 --flink_master=${FLINK_MASTER_URL} --environment_type=DOCKER --save_main_session --flink_submit_uber_jar
```

[Optionally] Open the flink web UI (this should open a tab in your browser).
```shell script
minikube service flink-jobmanager-rest
```

[Optionally] Tail the taskmanager logs.
```shell script
TASKMANAGER_POD=$(kubectl get pods --selector=component=taskmanager --no-headers -o name)
kubectl logs -f ${TASKMANAGER_POD} -c taskmanager
```


----

Beam Flink Job Server
---

> WIP: This is not currently working as-is!

It's also possible to use the `PortableRunner` you can submit to a beam-flink-jobserver running in k8s.

As of writing this, there seems to be a regression where the `--artifact_endpoint` is not working as intended (https://github.com/apache/beam/pull/12905). You'll need this small fix to submit to jobserver running in k8s.

```shell script
JOB_ENDPOINT=$(minikube service flink-beam-jobserver --url | sed '1q;d')
ARTIFACT_ENDPOINT=$(minikube service flink-beam-jobserver --url | sed '2q;d')
PYTHON_VERSION=$(python --version | cut -d" " -f2 | cut -d"." -f1-2)
BEAM_VERSION=$(python -c "import apache_beam;print(apache_beam.__version__)")
python -m pipeline --runner PortableRunner --job_endpoint ${JOB_ENDPOINT} --artifact_endpoint ${ARTIFACT_ENDPOINT} --save_main_session --environment_type DOCKER --environment_config apache/beam_python${PYTHON_VERSION}_sdk:${BEAM_VERSION}
```
