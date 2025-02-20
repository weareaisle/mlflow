from mlflow.entities.model_registry import (
    ModelVersion,
    ModelVersionTag,
    RegisteredModel,
    RegisteredModelAlias,
    RegisteredModelTag,
)
from mlflow.protos.databricks_uc_registry_messages_pb2 import ModelVersion as ProtoModelVersion
from mlflow.protos.databricks_uc_registry_messages_pb2 import (
    ModelVersionStatus as ProtoModelVersionStatus,
)
from mlflow.protos.databricks_uc_registry_messages_pb2 import (
    ModelVersionTag as ProtoModelVersionTag,
)
from mlflow.protos.databricks_uc_registry_messages_pb2 import (
    RegisteredModel as ProtoRegisteredModel,
)
from mlflow.protos.databricks_uc_registry_messages_pb2 import (
    RegisteredModelAlias as ProtoRegisteredModelAlias,
)
from mlflow.protos.databricks_uc_registry_messages_pb2 import (
    RegisteredModelTag as ProtoRegisteredModelTag,
)
from mlflow.store._unity_catalog.registry.utils import (
    model_version_from_uc_proto,
    registered_model_from_uc_proto,
)


def test_model_version_from_uc_proto():
    expected_model_version = ModelVersion(
        name="name",
        version="1",
        creation_timestamp=1,
        last_updated_timestamp=2,
        description="description",
        user_id="user_id",
        source="source",
        run_id="run_id",
        status="READY",
        status_message="status_message",
        aliases=["alias1", "alias2"],
        tags=[
            ModelVersionTag(key="key1", value="value"),
            ModelVersionTag(key="key2", value=""),
        ],
    )
    uc_proto = ProtoModelVersion(
        name="name",
        version="1",
        creation_timestamp=1,
        last_updated_timestamp=2,
        description="description",
        user_id="user_id",
        source="source",
        run_id="run_id",
        status=ProtoModelVersionStatus.Value("READY"),
        status_message="status_message",
        aliases=[
            ProtoRegisteredModelAlias(alias="alias1", version="1"),
            ProtoRegisteredModelAlias(alias="alias2", version="2"),
        ],
        tags=[
            ProtoModelVersionTag(key="key1", value="value"),
            ProtoModelVersionTag(key="key2", value=""),
        ],
    )
    actual_model_version = model_version_from_uc_proto(uc_proto)
    assert actual_model_version == expected_model_version


def test_registered_model_from_uc_proto():
    expected_registered_model = RegisteredModel(
        name="name",
        creation_timestamp=1,
        last_updated_timestamp=2,
        description="description",
        aliases=[
            RegisteredModelAlias(alias="alias1", version="1"),
            RegisteredModelAlias(alias="alias2", version="2"),
        ],
        tags=[
            RegisteredModelTag(key="key1", value="value"),
            RegisteredModelTag(key="key2", value=""),
        ],
    )
    uc_proto = ProtoRegisteredModel(
        name="name",
        creation_timestamp=1,
        last_updated_timestamp=2,
        description="description",
        aliases=[
            ProtoRegisteredModelAlias(alias="alias1", version="1"),
            ProtoRegisteredModelAlias(alias="alias2", version="2"),
        ],
        tags=[
            ProtoRegisteredModelTag(key="key1", value="value"),
            ProtoRegisteredModelTag(key="key2", value=""),
        ],
    )
    actual_registered_model = registered_model_from_uc_proto(uc_proto)
    assert actual_registered_model == expected_registered_model
