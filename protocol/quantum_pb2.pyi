from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Vector(_message.Message):
    __slots__ = ("id", "coordinates", "metadata", "quantum_state", "proof", "node_id", "timestamp")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ID_FIELD_NUMBER: _ClassVar[int]
    COORDINATES_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    QUANTUM_STATE_FIELD_NUMBER: _ClassVar[int]
    PROOF_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    id: str
    coordinates: _containers.RepeatedScalarFieldContainer[float]
    metadata: _containers.ScalarMap[str, str]
    quantum_state: QuantumState
    proof: bytes
    node_id: str
    timestamp: int
    def __init__(self, id: _Optional[str] = ..., coordinates: _Optional[_Iterable[float]] = ..., metadata: _Optional[_Mapping[str, str]] = ..., quantum_state: _Optional[_Union[QuantumState, _Mapping]] = ..., proof: _Optional[bytes] = ..., node_id: _Optional[str] = ..., timestamp: _Optional[int] = ...) -> None: ...

class QuantumState(_message.Message):
    __slots__ = ("state_data", "encoding", "parameters")
    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: float
        def __init__(self, key: _Optional[str] = ..., value: _Optional[float] = ...) -> None: ...
    STATE_DATA_FIELD_NUMBER: _ClassVar[int]
    ENCODING_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    state_data: bytes
    encoding: str
    parameters: _containers.ScalarMap[str, float]
    def __init__(self, state_data: _Optional[bytes] = ..., encoding: _Optional[str] = ..., parameters: _Optional[_Mapping[str, float]] = ...) -> None: ...

class CreateVectorRequest(_message.Message):
    __slots__ = ("coordinates", "metadata", "node_id")
    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    COORDINATES_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    NODE_ID_FIELD_NUMBER: _ClassVar[int]
    coordinates: _containers.RepeatedScalarFieldContainer[float]
    metadata: _containers.ScalarMap[str, str]
    node_id: str
    def __init__(self, coordinates: _Optional[_Iterable[float]] = ..., metadata: _Optional[_Mapping[str, str]] = ..., node_id: _Optional[str] = ...) -> None: ...

class VectorResponse(_message.Message):
    __slots__ = ("vector_id", "quantum_state", "proof", "status")
    VECTOR_ID_FIELD_NUMBER: _ClassVar[int]
    QUANTUM_STATE_FIELD_NUMBER: _ClassVar[int]
    PROOF_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    vector_id: str
    quantum_state: QuantumState
    proof: bytes
    status: str
    def __init__(self, vector_id: _Optional[str] = ..., quantum_state: _Optional[_Union[QuantumState, _Mapping]] = ..., proof: _Optional[bytes] = ..., status: _Optional[str] = ...) -> None: ...

class VerifyVectorRequest(_message.Message):
    __slots__ = ("vector_id", "proof")
    VECTOR_ID_FIELD_NUMBER: _ClassVar[int]
    PROOF_FIELD_NUMBER: _ClassVar[int]
    vector_id: str
    proof: bytes
    def __init__(self, vector_id: _Optional[str] = ..., proof: _Optional[bytes] = ...) -> None: ...

class VerificationResponse(_message.Message):
    __slots__ = ("valid", "message")
    VALID_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    valid: bool
    message: str
    def __init__(self, valid: bool = ..., message: _Optional[str] = ...) -> None: ...

class ProofRequest(_message.Message):
    __slots__ = ("vector_id",)
    VECTOR_ID_FIELD_NUMBER: _ClassVar[int]
    vector_id: str
    def __init__(self, vector_id: _Optional[str] = ...) -> None: ...

class ProofResponse(_message.Message):
    __slots__ = ("proof", "quantum_state")
    PROOF_FIELD_NUMBER: _ClassVar[int]
    QUANTUM_STATE_FIELD_NUMBER: _ClassVar[int]
    proof: bytes
    quantum_state: QuantumState
    def __init__(self, proof: _Optional[bytes] = ..., quantum_state: _Optional[_Union[QuantumState, _Mapping]] = ...) -> None: ...

class QuantumOperationRequest(_message.Message):
    __slots__ = ("operation", "parameters", "vector_ids")
    class ParametersEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: bytes
        def __init__(self, key: _Optional[str] = ..., value: _Optional[bytes] = ...) -> None: ...
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    VECTOR_IDS_FIELD_NUMBER: _ClassVar[int]
    operation: str
    parameters: _containers.ScalarMap[str, bytes]
    vector_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, operation: _Optional[str] = ..., parameters: _Optional[_Mapping[str, bytes]] = ..., vector_ids: _Optional[_Iterable[str]] = ...) -> None: ...

class QuantumOperationResponse(_message.Message):
    __slots__ = ("result", "status", "additional_data")
    class AdditionalDataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: bytes
        def __init__(self, key: _Optional[str] = ..., value: _Optional[bytes] = ...) -> None: ...
    RESULT_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ADDITIONAL_DATA_FIELD_NUMBER: _ClassVar[int]
    result: bytes
    status: str
    additional_data: _containers.ScalarMap[str, bytes]
    def __init__(self, result: _Optional[bytes] = ..., status: _Optional[str] = ..., additional_data: _Optional[_Mapping[str, bytes]] = ...) -> None: ...

class VectorFilter(_message.Message):
    __slots__ = ("vector_ids", "node_ids", "since_timestamp")
    VECTOR_IDS_FIELD_NUMBER: _ClassVar[int]
    NODE_IDS_FIELD_NUMBER: _ClassVar[int]
    SINCE_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    vector_ids: _containers.RepeatedScalarFieldContainer[str]
    node_ids: _containers.RepeatedScalarFieldContainer[str]
    since_timestamp: int
    def __init__(self, vector_ids: _Optional[_Iterable[str]] = ..., node_ids: _Optional[_Iterable[str]] = ..., since_timestamp: _Optional[int] = ...) -> None: ...

class VectorUpdate(_message.Message):
    __slots__ = ("update_type", "vector", "proof", "timestamp")
    UPDATE_TYPE_FIELD_NUMBER: _ClassVar[int]
    VECTOR_FIELD_NUMBER: _ClassVar[int]
    PROOF_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    update_type: str
    vector: Vector
    proof: bytes
    timestamp: int
    def __init__(self, update_type: _Optional[str] = ..., vector: _Optional[_Union[Vector, _Mapping]] = ..., proof: _Optional[bytes] = ..., timestamp: _Optional[int] = ...) -> None: ...
