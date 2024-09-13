#
# Copyright (c) 2023 Airbyte, Inc., all rights reserved.
#

"""This modules groups functions made to download/upload secrets from/to a remote secret service and provide these secret in a dagger Directory."""
from __future__ import annotations

from typing import TYPE_CHECKING

from pipelines.helpers.utils import get_secret_host_variable
from pipelines.models.secrets import Secret

if TYPE_CHECKING:
    from typing import Callable, List

    from dagger import Container
    from pipelines.airbyte_ci.connectors.context import ConnectorContext


# TODO deprecate to use Secret and SecretStores
# Not prioritized as few connectors have to export their secrets back to GSM
# This would require exposing a secret update interface on the SecretStore
# and a more complex structure / Logic to map container files to Secret objects
async def upload(context: ConnectorContext, gcp_gsm_env_variable_name: str = "GCP_GSM_CREDENTIALS") -> Container:
    """Use the ci-credentials tool to upload the secrets stored in the context's updated_secrets-dir.

    Args:
        context (ConnectorContext): The context providing a connector object and the update secrets dir.
        gcp_gsm_env_variable_name (str, optional): The name of the environment variable holding credentials to connect to Google Secret Manager. Defaults to "GCP_GSM_CREDENTIALS".

    Returns:
        container (Container): The executed ci-credentials update-secrets command.

    Raises:
        ExecError: If the command returns a non-zero exit code.
    """
    assert context.updated_secrets_dir is not None, "The context's updated_secrets_dir must be set to upload secrets."
    # temp - fix circular import
    from pipelines.dagger.containers.internal_tools import with_ci_credentials

    gsm_secret = get_secret_host_variable(context.dagger_client, gcp_gsm_env_variable_name)
    secrets_path = f"/{context.connector.code_directory}/secrets"

    ci_credentials = await with_ci_credentials(context, gsm_secret)

    return await ci_credentials.with_directory(secrets_path, context.updated_secrets_dir).with_exec(
        ["ci_credentials", context.connector.technical_name, "update-secrets"]
    )


async def mounted_connector_secrets(
    context: ConnectorContext, secret_directory_path: str, connector_secrets: List[Secret]
) -> Callable[[Container], Container]:
    """Returns an argument for a dagger container's with_ method which mounts all connector secrets in it.

    Args:
        context (ConnectorContext): The context providing a connector object and its secrets.
        secret_directory_path (str): Container directory where the secrets will be mounted, as files.
        connector_secrets (List[secrets]): List of secrets to mount to the connector container.
    Returns:
        fn (Callable[[Container], Container]): A function to pass as argument to the connector container's with_ method.
    """
    java_log_scrub_pattern_secret = context.java_log_scrub_pattern_secret

    def with_secrets_mounted_as_dagger_secrets(container: Container) -> Container:
        if java_log_scrub_pattern_secret:
            # This LOG_SCRUB_PATTERN environment variable is used by our log4j test configuration
            # to scrub secrets from the log messages. Although we already ensure that github scrubs them
            # from its runner logs, this is required to prevent the secrets from leaking into gradle scans,
            # test reports or any other build artifacts generated by a java connector test.
            container = container.with_secret_variable("LOG_SCRUB_PATTERN", java_log_scrub_pattern_secret)
        container = container.with_exec(["mkdir", "-p", secret_directory_path], skip_entrypoint=True)
        for secret in connector_secrets:
            if secret.file_name:
                container = container.with_mounted_secret(
                    f"{secret_directory_path}/{secret.file_name}", secret.as_dagger_secret(context.dagger_client)
                )
        return container

    return with_secrets_mounted_as_dagger_secrets