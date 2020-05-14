# Graphviz Cobra Docker Container

Running the tool locally means installing dependencies like Graphviz and ACI Cobra SDK. To avoid the hassle, use a Docker container that comes with the tool script and all the dependencies pre-packaged. Container is available in [DockerHub](https://hub.docker.com/repository/docker/vasilyprokopov/acigraphvizcobra) and has a size of around 500 MB uncompressed.

## Usage

Use Docker to run a container, and mount your local directory that you want the output diagram to appear in:

```
docker run --rm -ti \
-v <localdirectory>:/home/out \
vasilyprokopov/acigraphvizcobra:5.0 bash
```

Docker will take care of downloading a Graphviz Cobra container from DockerHub.

### Usage examples:

In the running container execute the tool similar to the examples below:
```
python /home/aci-graphviz-cobra/aci-graphviz-cobra.py
```
```
python /home/aci-graphviz-cobra/aci-graphviz-cobra.py \
-a https://169.254.1.1 -u admin -p pass31339 \
-t graphviz1_tn graphviz3_tn graphviz2_tn
```
```
python /home/aci-graphviz-cobra/aci-graphviz-cobra.py \
-a https://169.254.1.1 \
-c uni/userext/user-admin/usercert-admin_crt -k /home/out/admin.key \
-t graphviz1_tn graphviz3_tn graphviz2_tn
```
After the successful run find your diagram in ```/home/out``` directory as well as in your local directory attached to a container
To be able to use certificate-base authentication make sure to put your private key in your local directory attached to a container.

## How is it packaged?
Image file [aci-graphviz-cobra.app](aci-graphviz-cobra.app) is available in this repository.
Base image is ```python:3.7.3-slim```, which is small in size (143 MB) and based on Debian.
The script depends on ```pygraphviz```, which requires ```graphviz``` and ```libgraphviz-dev```.
The script also depends on ACI Cobra SDK – ```acicobra``` and ```acimodel```, that are also added to the image.
To be able to pull the script from GitHub ```git``` is added to the image.

After the dependencies have been installed, we pull the script from GitHub and create a link between the ```/out``` subdirectory and ```/home/out``` directory, that in turn points to your local directory attached to a container:
```
ln -s /home/out /home/aci-graphviz-cobra
```
To reduce the size of a container we then remove ```libgraphviz-dev``` and ```git```.

Cobra SDK consumes around 800 MB of space, but only small subset of SDK objects are being used by the script. Hence, we are removing some of the unused objects, like the one below:
```
rm -rf /usr/local/lib/python3.7/site-packages/cobra/modelimpl/cloudsec
```
We also clear Python's cache, as it is worth another 300 MB but barely adding any performance benefit.
```
find /usr/local/lib/python3.7/site-packages/cobra/modelimpl/ | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf
```
Finally, we remove Cobra's installation files, that were imported into the image in the beggining.
This makes the size of resulting container less then 500 MB, while when built without proper cleaning, the container size can easily outgrow 1 GB.

All Linux commands are being put under the single ```RUN``` on purpose - to remove unnecessary container layers. Not a perfect solution, but [multi-stage](https://pythonspeed.com/articles/smaller-python-docker-images/) build, which might have been a better alternative, has limited applicability to our use case.

From within the build directory create a container:
```
docker build -t acigraphvizcobra:5.0 -f aci-graphviz-cobra.app .
```

## Author

[**Vasily Prokopov**](https://github.com/vasilyprokopov)
