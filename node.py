# quantum_node.py
from concurrent import futures
import grpc
import numpy as np
from typing import Dict, Any
import time

from modules.vectorchain import LocalVectorNode
from settings import load_config, VectorSettings
from protocol.quantum_pb2 import *
from protocol.quantum_pb2_grpc import QuantumNodeServicer, add_QuantumNodeServicer_to_server

from modules.crypto_module import KeyManagement
from modules.vector_module import QuantumVectorManager


class QuantumNodeService(QuantumNodeServicer):
    def __init__(self, config: Dict[str, Any]):
        self.vector_node = LocalVectorNode(config)
        self.key_manager = KeyManagement()
        self.vector_manager = QuantumVectorManager(config.get('vector'))

    async def CreateVector(self, request, context):
        try:
            coordinates = np.array(request.coordinates)
            metadata = dict(request.metadata)

            result = await self.vector_node.create_vector(coordinates.tolist(), metadata)

            return VectorResponse(
                vector_id=result["vector_id"],
                quantum_state=QuantumState(
                    state_data=result["quantum_state"]["data"],
                    encoding=result["quantum_state"]["encoding"],
                    parameters=result["quantum_state"]["parameters"]
                ),
                proof=result["proof"],
                status="success"
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return VectorResponse()

    async def VerifyVector(self, request, context):
        try:
            result = await self.vector_node.verify_vector(
                request.vector_id,
                request.proof
            )
            return VerificationResponse(
                valid=result["valid"],
                message=result.get("message", "")
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return VerificationResponse()

    async def ProcessQuantumOperation(self, request, context):
        try:
            result = await self.vector_node.process_quantum_operation(
                request.operation,
                {k: v for k, v in request.parameters.items()}
            )
            return QuantumOperationResponse(
                result=result["result"],
                status=result["status"],
                additional_data=result.get("additional_data", {})
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return QuantumOperationResponse()

    async def SubscribeToVectorUpdates(self, request, context):
        try:
            async for update in self.vector_node.subscribe_to_updates(
                    request.vector_ids,
                    request.node_ids,
                    request.since_timestamp
            ):
                yield VectorUpdate(
                    update_type=update["type"],
                    vector=Vector(
                        id=update["vector"]["id"],
                        coordinates=update["vector"]["coordinates"],
                        metadata=update["vector"]["metadata"],
                        quantum_state=QuantumState(**update["vector"]["quantum_state"]),
                        proof=update["vector"]["proof"],
                        node_id=update["vector"]["node_id"],
                        timestamp=update["vector"]["timestamp"]
                    ),
                    proof=update["proof"],
                    timestamp=update["timestamp"]
                )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return


def serve(config: Dict[str, Any]):
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    add_QuantumNodeServicer_to_server(QuantumNodeService(config), server)
    server.add_insecure_port('[::]:50051')
    return server


async def main():
    config = load_config()

    server = serve(config)
    await server.start()
    await server.wait_for_termination()


if __name__ == '__main__':
    import asyncio

    asyncio.run(main(), debug=True)