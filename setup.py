import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
     name='rpi_bluemaestro_mqtt',
     version='0.1',
     scripts=['bluemaestro_mqtt'] ,
     author="Nathan Eaton",
     author_email="nate.eaton.jr@gmail.com",
     description="A Blue Maestro sensor package",
     long_description=long_description,
     long_description_content_type="text/markdown",
     url="https://github.com/NateEaton/rpi_bluemaestro_mqtt",
     packages=setuptools.find_packages(),
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
     ],
 )
