import aws_cdk
from aws_cdk import Stack
from constructs import Construct
from aws_cdk import aws_iam
from aws_cdk.pipelines import CodePipeline
from aws_cdk.pipelines import CodePipelineSource
from aws_cdk.pipelines import ShellStep
from aws_cdk.pipelines import CodeBuildStep
from aws_cdk import aws_codebuild
from aws_cdk import aws_ecr
from constructs import Construct
from _stacks.build_spec import build_spec_object


class PipelineStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, env: aws_cdk.Environment, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        repository_name = self.node.try_get_context('github_repository_name')
        github_connection_arn = self.node.try_get_context('github_connection_arn')

        github_connection = CodePipelineSource.connection(
            repo_string=repository_name,
            branch='master',
            connection_arn=github_connection_arn
        )

        ecr_pipeline = CodePipeline(
            scope=self,
            id='EcrPipeline',
            pipeline_name='ecr_pipeline',
            # self_mutation=False,  # UpdatePipeline　Stageがなくなる。
            synth=ShellStep(
                id='Synth',
                input=github_connection,
                commands=[
                    'npm install -g aws-cdk',
                    'python -m pip install -r requirements.txt',
                    'cdk synth'
                ]
            )
        )

        # ---------------------------------------------------------
        #  Stage 追加
        #  ECR Repository作成 と Docker Build & Push
        # ---------------------------------------------------------

        # ecr_repository_name = self.node.try_get_context('ecr_repository_name')
        #
        # ecr_repo = aws_ecr.Repository(
        #     self,
        #     'SamplePythonAppRepo',
        #     repository_name=ecr_repository_name,
        #     image_scan_on_push=True,  # Image Scan
        #     # removal_policy=aws_cdk.RemovalPolicy.DESTROY, # stack削除時の動作
        #     # lifecycle_rules=[removal_old_image]  # imageの世代管理
        # )

        # ---------------------------------------------------------
        #  Stage にはStackとStepを追加する
        #  StackはCDK Stackのことである。
        #  StageにCDK Stackを入れる
        # ---------------------------------------------------------

        # ----------------------------------------
        # Stage - Policy
        # ----------------------------------------
        ecr_policy = aws_iam.PolicyStatement(
            actions=[
                # 'codebuild:*',
                'ecr:PutImage',
                'ecr:BatchCheckLayerAvailability',
                'ecr:CompleteLayerUpload',
                'ecr:InitiateLayerUpload',
                'ecr:UploadLayerPart',
                'ecr:GetAuthorizationToken'
            ],
            effect=aws_iam.Effect.ALLOW,
            resources=['*']
        )
        ssm_policy = aws_iam.PolicyStatement(
            effect=aws_iam.Effect.ALLOW,
            actions=['ssm:GetParameter', 'ssm:GetParameters'],
            resources=[f'arn:aws:ssm:{self.region}:{self.account}:parameter/*']
        )
        logs_policy = aws_iam.PolicyStatement(
            actions=['logs:GetLogEvents'],
            effect=aws_iam.Effect.ALLOW,
            resources=[f'arn:aws:logs:{self.region}:{self.account}:log-group:/aws/codebuild/*:*']
        )
        # ----------------------------------------

        ecr_repo_stage = EcrRepositoryStage(
            scope=self,
            construct_id='SampleAppEcrRepoStage',
            env=env
        )

        build_spec = aws_codebuild.BuildSpec.from_object(build_spec_object)
        ecr_repository_name = self.node.try_get_context('ecr_repository_name')
        build_container_project = CodeBuildStep(
            id='DockerBuildStep',
            build_environment=aws_codebuild.BuildEnvironment(
                                build_image=aws_codebuild.LinuxBuildImage.STANDARD_5_0,
                                privileged=True),  # for docker build
            input=github_connection,
            partial_build_spec=build_spec,
            commands=[],  # need empty by partial_build_spec,
            role_policy_statements=[
                ecr_policy,
                logs_policy,
                ssm_policy
            ],
            env={
                'AWS_ACCOUNT_ID': self.account,
                'CONTAINER_IMAGE_NAME': ecr_repository_name,
            }
        )

        ecr_pipeline.add_stage(
            stage=ecr_repo_stage,
            post=[build_container_project],
        )

        # ecr_repo_actions = ["ecr:PutImage",
        #                     "ecr:BatchCheckLayerAvailability",
        #                     "ecr:CompleteLayerUpload",
        #                     "ecr:InitiateLayerUpload",
        #                     "ecr:UploadLayerPart"]
        #
        # for perm in ecr_repo_actions:
        #     ecr_repo.grant(buildContainerProject, perm)
        #
        # _iam.Grant.add_to_principal(
        #     actions=["ecr:GetAuthorizationToken"],
        #     resource_arns=["*"],
        #     grantee=buildContainerProject
        # )


class EcrRepositoryStage(aws_cdk.Stage):
    # ---------------------------------------------------------
    #  Stage にはStackとStepを追加する
    #  StackはCDK Stackのことである。
    #  StageにCDK Stackを入れる
    # ---------------------------------------------------------
    def __init__(self,
                 scope: Construct,
                 construct_id: str,
                 env: aws_cdk.Environment,
                 **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        self.__ecr_repo_stack = EcrRepositoryStack(
            scope=self,
            construct_id=construct_id,
            env=env
        )

    @property
    def ecr_repo_stack(self):
        return self.__ecr_repo_stack


class EcrRepositoryStack(aws_cdk.Stack):
    # ---------------------------------------------------------
    #  Stageに追加するStack
    #  StackはCDK Stackのことである。
    # ---------------------------------------------------------
    def __init__(self,
                 scope: Construct,
                 construct_id: str,
                 env: aws_cdk.Environment,
                 **kwargs) -> None:

        super().__init__(scope, construct_id, **kwargs)

        ecr_repository_name = self.node.try_get_context('ecr_repository_name')
        aws_ecr.Repository(
            scope=self,
            id=f'{ecr_repository_name}-Stack',
            repository_name=ecr_repository_name,
            image_scan_on_push=True,  # Image Scan
            # removal_policy=aws_cdk.RemovalPolicy.DESTROY, # stack削除時の動作
            # lifecycle_rules=[removal_old_image]  # imageの世代管理
        )

