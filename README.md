# Beam Flink & Kubernetes

This repo is a bare minimum sample of running a python beam pipeline on flink deployed in a kubernetes cluster.

## Setup (via minikube)

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

## Deployment


You can deploy flink with or without a job server. If you deploy without, you must run your pipeline using the `FlinkRunner` along with the option `--flink_submit_uber_jar`. 
The `FlinkRunner` will start a local job service via java and expects the client to have java install. Using `flink_submit_uber_jar` will pack all artifacts into the jar file it uploads to flink. This is required due to the local job server and the flink taskmanager not sharing the staging volume.

Alternatively you can deploy a job service into the k8s cluster and run your pipeline using the `PortableRunner`. This requires a more complicated k8s deployment because we must share volume between the job service and the flink taskmanager.


### Flink With No Job Server

Deploy the flink components to kubernetes.
```shell script
kubectl apply -f ./k8s/without_job_server/flink.yaml
```

Wait a minute for the pods to spin up.
```shell script
kubectl get pods
```

Submit a beam pipeline.
```shell script
FLINK_MASTER_URL=$(minikube service flink-jobmanager-rest --url)
python -m pipeline --runner=FlinkRunner --flink_version 1.10 --flink_master=${FLINK_MASTER_URL} --environment_type=DOCKER --save_main_session --flink_submit_uber_jar
```


### Flink With Job Server

It's also possible to use the `PortableRunner` by submitting the pipeline to a job server running in k8s.

The job server and the flink taskmanagers need to share the same artifact staging volume. This is necessary so the sdk harness can find the artifacts.

First deploy the persistent volumes and claims.
```shell script
kubectl apply -f ./k8s/with_job_server/shared.yaml
```

Then deploy flink.
```shell script
kubectl apply -f ./k8s/with_job_server/flink.yaml
```

Last deploy the job server.
```shell script
kubectl apply -f ./k8s/with_job_server/beam_flink_job_server.yaml
```

Submit a beam pipeline.
```shell script
JOB_ENDPOINT=$(minikube service flink-beam-jobserver --url | sed '1q;d')
ARTIFACT_ENDPOINT=$(minikube service flink-beam-jobserver --url | sed '2q;d')
PYTHON_VERSION=$(python --version | cut -d" " -f2 | cut -d"." -f1-2)
BEAM_VERSION=$(python -c "import apache_beam;print(apache_beam.__version__)")
python -m pipeline --runner=PortableRunner --job_endpoint=${JOB_ENDPOINT} --artifact_endpoint=${ARTIFACT_ENDPOINT} --save_main_session --environment_type=DOCKER --environment_config=apache/beam_python${PYTHON_VERSION}_sdk:${BEAM_VERSION}
```


## Tips, Monitoring, & Debugging

[TIP] Pre-download the sdk container in the docker-in-docker service on the taskworker. If you don't do this then the taskworker may timeout waiting for the sdk container to spin up.
```shell script
PYTHON_VERSION=$(python --version | cut -d" " -f2 | cut -d"." -f1-2)
BEAM_VERSION=$(python -c "import apache_beam;print(apache_beam.__version__)")
TASKMANAGER_POD=$(kubectl get pods --selector=component=taskmanager --no-headers -o name)
kubectl exec ${TASKMANAGER_POD} -c taskmanager -- docker pull apache/beam_python${PYTHON_VERSION}_sdk:${BEAM_VERSION}
```

Open the flink web UI (this should open a tab in your browser).
```shell script
minikube service flink-jobmanager-rest
```

Tail the taskmanager logs.
```shell script
TASKMANAGER_POD=$(kubectl get pods --selector=component=taskmanager --no-headers -o name)
kubectl logs -f ${TASKMANAGER_POD} -c taskmanager
```

Tail SDK Harness logs.
```shell script
TASKMANAGER_POD=$(kubectl get pods --selector=component=taskmanager --no-headers -o name)
kubectl exec -it ${TASKMANAGER_POD} -c taskmanager -- bash
docker logs -f $(docker ps -lq)
```
