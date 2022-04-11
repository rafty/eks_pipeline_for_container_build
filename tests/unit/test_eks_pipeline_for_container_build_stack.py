import aws_cdk as core
import aws_cdk.assertions as assertions

from _stacks.pipeline import EksPipelineForContainerBuildStack

# example tests. To run these tests, uncomment this file along with the example
# resource in _stacks/pipeline.py
def test_sqs_queue_created():
    app = core.App()
    stack = EksPipelineForContainerBuildStack(app, "eks-pipeline-for-container-build")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
