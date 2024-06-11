FROM python:3.9-alpine
# FROM public.ecr.aws/amazonlinux/amazonlinux:latest
# FROM public.ecr.aws/sam/build-python3.9:latest
# FROM public.ecr.aws/lambda/python:3.9

RUN pip3 install awscli --force-reinstall --upgrade  # for AWS CLI to download requirements.txt

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY app.py app.py

# CMD ["aws", "sts", "get-caller-identity"]  # works
# ENTRYPOINT ["sleep", "inf"]  # for testing with ECS exec enabled
# CMD ["aws", "s3", "cp", "s3://mwaa-practice-bucket/dags/ecs_requirements.txt", ".", "&&", "ls"]  # works
# ENTRYPOINT ["aws", "s3", "cp", "s3://mwaa-practice-bucket/dags/ecs_requirements.txt", ".", "&&", "ls"]  # works
# ENTRYPOINT [\  # works
#     "/bin/sh", "-c" , "pip3 freeze \
#     && aws s3 cp s3://mwaa-practice-bucket/dags/ecs_requirements.txt . \
#     && pip3 install -r ecs_requirements.txt \
#     && pip3 freeze \
#     # && ls \
#     # && black app.py \
#     && python3 app.py" \
# ]
ENTRYPOINT ["/bin/sh", "-c"]

# CMD ["python3", "app.py"]
