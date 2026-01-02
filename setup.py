import setuptools

version = "0.1.0"

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ttdiagnosis",
    version=version,
    author="Tychetools",
    description="Tychetools diagnosis tool for gateway",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://bitbucket.org/tychetools/gw-misc/src/master/ttdiagnosis/",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.7",
    #TODO do not requiere request as it uses http_helper from gw-app
    #     but it is not mandatory, if not available, backend
    #     funcionality is disabled
    install_requires=[
        "ttgateway==1.14.3",
    ],
    entry_points={
        "console_scripts": {
            "run_ttdiagnosis = ttdiagnosis.__init__:run",
            "start_ttdiagnosis = ttdiagnosis.__init__:start",
        }
    },
)
