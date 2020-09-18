Beam Flink & Kubernetes
---

This repo is a bare minimum sample of running a python beam pipeline on flink deployed in a kubernetes cluster.

Setup (via minikube)
-----

This assumes you're starting in an environment with python, a recent version of beam installed, and [minikube](https://kubernetes.io/docs/tasks/tools/install-minikube/). 

Start up a simple minikube k8s cluster
```shell script
minikube start --cpus 4 --memory='6gb' --disk-size='20gb'
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
\# TODO

Using the `PortableRunner` you can submit to a beam-flink-jobserver running in k8s. When whipping this example up I didn't test that this was working but left in some pieces for those interested.

A big challenge is that the taskmanager needs to share the artifact staging volume with the artifact service which runs as part of the jobservice. This is the same reason we need to provide `--flink_submit_uber_jar` using the `FlinkRunner` when providing any artifacts (e.g. `--save_main_session`). I'm not sure if newer versions of beam provide alternative ways to pass the artifacts, but that is an improvement that could be made.