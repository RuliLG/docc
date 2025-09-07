from setuptools import setup, find_packages

setup(
    name="docc",
    version="1.0.0",
    description="Documentation tool with UI",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.5.0",
        "httpx>=0.25.2",
        "python-multipart>=0.0.6",
        "anthropic>=0.7.7",
        "openai>=1.3.7",
        "elevenlabs>=0.2.26",
    ],
    python_requires=">=3.8",
)