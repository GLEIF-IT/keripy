"""Shared TCP connections and TLS credentials for transport tests."""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import ipaddress
import socket

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from hio.core.tcp import serving


def makeRemoter(ims=b"", *, cutoff=False, cs=None, tymeout=None):
    """Create an accepted connection buffer for direct Reactant tests."""
    remoter = serving.Remoter(ha=("127.0.0.1", 5632), ca=("127.0.0.1", 5633),
                              cs=cs, tymeout=tymeout)
    remoter.rxbs.extend(ims)
    remoter.cutoff = cutoff
    return remoter


@contextmanager
def openTcpPair(ims=b"", *, tymeout=None):
    """Own a Server, a socket-backed Remoter, and its peer for one test.
    Simulates the normal HIO management of TCP connections that are consumed and
    supervised by KERIpy components like Director and Reactant.

    The caller registers and winds the Remoter after scheduler entry, since
    ServerDoer.enter() reopens the server and closes existing connections.
    """
    remoterSocket, peerSocket = socket.socketpair()
    with remoterSocket, peerSocket:
        remoter = makeRemoter(ims, cs=remoterSocket, tymeout=tymeout)
        server = serving.Server(host="127.0.0.1", port=0, tymeout=tymeout)
        try:
            yield server, remoter, peerSocket
        finally:
            server.close()


@pytest.fixture(scope="module")
def witnessTlsFiles(tmp_path_factory):
    """Create a temporary key and self-signed certificate for loopback TLS tests."""
    path = tmp_path_factory.mktemp("witness-tls")
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    now = datetime.now(timezone.utc)

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)  # The test certificate signs itself.
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=1))
        # The client connects by IP, so certificate verification needs an IP SAN.
        .add_extension(
            x509.SubjectAlternativeName([
                x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
            ]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    keypath, certpath = path / "key.pem", path / "cert.pem"
    keypath.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    certpath.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

    # Trust this self-signed certificate when the client verifies the server.
    return dict(
        keypath=str(keypath),
        certpath=str(certpath),
        cafilepath=str(certpath),
    )
