import setuptools

setuptools.setup(
    name="awstack",
    version="0.1.0",
    description="aws cloudformation for humans",
    url="https://github.com/mazaziz/awstack",
    author="Aziz Maz",
    author_email="mazaziz@gmail.com",
    license="Apache Software License",
    packages=setuptools.find_packages(),
    install_requires=["docopt", "boto3"],
    python_requires="~=3.6",
    entry_points={
        "console_scripts": [
            "awstack = awstack.cli:main"
        ]
    }
)
