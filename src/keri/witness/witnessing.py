# -*- encoding: utf-8 -*-
"""
keri.witness.witnessing module

Witness server-side functionality for KERI protocol.
"""
import platform
import time
import falcon

from hio.base import doing
from hio.core import http, tcp
from hio.core.tcp import serving
from hio.help import decking

import keri.app.oobiing
from keri.app import directing, storing, httping, forwarding, oobiing
from keri import help, kering
from keri.core import eventing, parsing, routing, coring, serdering, Counter, Codens
from keri.core.coring import Ilks
from keri.db import basing, dbing
from keri.end import ending
from keri.peer import exchanging
from keri.vdr import verifying, viring
from keri.vdr.eventing import Tevery

logger = help.ogler.getLogger()


def setupWitness(hby, alias="witness", mbx=None, aids=None, tcpPort=5631, httpPort=5632,
                 keypath=None, certpath=None, cafilepath=None):
    """
    Setup witness controller and doers

    """
    host = "0.0.0.0"
    if platform.system() == "Windows":
        host = "127.0.0.1"
    cues = decking.Deck()
    doers = []

    # make hab
    hab = hby.habByName(name=alias)
    if hab is None:
        hab = hby.makeHab(name=alias, transferable=False)

    reger = viring.Reger(name=hab.name, db=hab.db, temp=False)
    verfer = verifying.Verifier(hby=hby, reger=reger)

    mbx = mbx if mbx is not None else storing.Mailboxer(name=alias, temp=hby.temp)
    forwarder = forwarding.ForwardHandler(hby=hby, mbx=mbx)
    exchanger = exchanging.Exchanger(hby=hby, handlers=[forwarder])
    clienter = httping.Clienter()
    oobiery = keri.app.oobiing.Oobiery(hby=hby, clienter=clienter)

    app = falcon.App(cors_enable=True)
    ending.loadEnds(app=app, hby=hby, default=hab.pre)
    oobiing.loadEnds(app=app, hby=hby, prefix="/ext")
    rep = storing.Respondant(hby=hby, mbx=mbx, aids=aids)

    rvy = routing.Revery(db=hby.db, cues=cues)
    kvy = eventing.Kevery(db=hby.db,
                          lax=True,
                          local=False,
                          rvy=rvy,
                          cues=cues)
    kvy.registerReplyRoutes(router=rvy.rtr)

    tvy = Tevery(reger=verfer.reger,
                 db=hby.db,
                 local=False,
                 cues=cues)

    tvy.registerReplyRoutes(router=rvy.rtr)
    parser = parsing.Parser(framed=True,
                            kvy=kvy,
                            tvy=tvy,
                            exc=exchanger,
                            rvy=rvy)

    httpEnd = HttpEnd(rxbs=parser.ims, mbx=mbx)
    app.add_route("/", httpEnd)
    receiptEnd = ReceiptEnd(hab=hab, inbound=cues, aids=aids)
    app.add_route("/receipts", receiptEnd)
    queryEnd = QueryEnd(hab=hab)
    app.add_route("/query", queryEnd)

    server = createHttpServer(host, httpPort, app, keypath, certpath, cafilepath)
    if not server.reopen():
        raise RuntimeError(f"cannot create http server on port {httpPort}")
    httpServerDoer = http.ServerDoer(server=server)

    # setup doers
    regDoer = basing.BaserDoer(baser=verfer.reger)

    if tcpPort is not None:
        server = serving.Server(host="", port=tcpPort)
        if not server.reopen():
            raise RuntimeError(f"cannot create tcp server on port {tcpPort}")
        serverDoer = serving.ServerDoer(server=server)

        directant = directing.Directant(hab=hab, server=server, verifier=verfer)
        doers.extend([directant, serverDoer])

    witStart = WitnessStart(hab=hab, parser=parser, cues=receiptEnd.outbound,
                            kvy=kvy, tvy=tvy, rvy=rvy, exc=exchanger, replies=rep.reps,
                            responses=rep.cues, queries=httpEnd.qrycues)

    doers.extend([regDoer, httpServerDoer, rep, witStart, receiptEnd, *oobiery.doers])
    return doers


def createHttpServer(host, port, app, keypath=None, certpath=None, cafilepath=None):
    """
    Create an HTTP or HTTPS server depending on whether TLS key material is present
    Parameters:
        host(str)          : host to bind to for this server, or None for default of '0.0.0.0', all ifaces
        port (int)         : port to listen on for all HTTP(s) server instances
        app (Any)          : WSGI application instance to pass to the http.Server instance
        keypath (string)   : the file path to the TLS private key
        certpath (string)  : the file path to the TLS signed certificate (public key)
        cafilepath (string): the file path to the TLS CA certificate chain file
    Returns:
        hio.core.http.Server
    """
    if keypath is not None and certpath is not None and cafilepath is not None:
        servant = tcp.ServerTls(certify=False,
                                keypath=keypath,
                                certpath=certpath,
                                cafilepath=cafilepath,
                                port=port)
        server = http.Server(host=host, port=port, app=app, servant=servant)
    else:
        server = http.Server(host=host, port=port, app=app)
    return server


class WitnessStart(doing.DoDoer):
    """ Doer to print witness prefix after initialization

    """

    def __init__(self, hab, parser, kvy, tvy, rvy, exc, cues=None, replies=None, responses=None, queries=None, **opts):
        self.hab = hab
        self.parser = parser
        self.kvy = kvy
        self.tvy = tvy
        self.rvy = rvy
        self.exc = exc
        self.queries = queries if queries is not None else decking.Deck()
        self.replies = replies if replies is not None else decking.Deck()
        self.responses = responses if responses is not None else decking.Deck()
        self.cues = cues if cues is not None else decking.Deck()

        doers = [doing.doify(self.start), doing.doify(self.msgDo), doing.doify(self.escrowDo), doing.doify(self.cueDo)]
        super().__init__(doers=doers, **opts)

    def start(self, tymth=None, tock=0.0, **kwa):
        """ Prints witness name and prefix

        Parameters:
            tymth (function): injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock (float): injected initial tock value

        """
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        while not self.hab.inited:
            yield self.tock

        print("Witness", self.hab.name, ":", self.hab.pre)

    def msgDo(self, tymth=None, tock=0.0, **kwa):
        """
        Returns doifiable Doist compatibile generator method (doer dog) to process
            incoming message stream of .kevery

        Parameters:
            tymth (function): injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock (float): injected initial tock value

        Usage:
            add result of doify on this method to doers list
        """
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        if self.parser.ims:
            logger.debug("Client %s received:\n%s\n...\n", self.kvy, self.parser.ims[:1024])
        done = yield from self.parser.parsator(local=True)  # process messages continuously
        return done  # should nover get here except forced close

    def escrowDo(self, tymth=None, tock=0.0, **kwa):
        """
         Returns doifiable Doist compatibile generator method (doer dog) to process
            .kevery and .tevery escrows.

        Parameters:
            tymth (function): injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock (float): injected initial tock value

        Usage:
            add result of doify on this method to doers list
        """
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        while True:
            self.kvy.processEscrows()
            self.rvy.processEscrowReply()
            if self.tvy is not None:
                self.tvy.processEscrows()
            self.exc.processEscrow()

            yield

    def cueDo(self, tymth=None, tock=0.0, **kwa):
        """
         Returns doifiable Doist compatibile generator method (doer dog) to process
            .kevery.cues deque

        Doist Injected Attributes:
            g.tock = tock  # default tock attributes
            g.done = None  # default done state
            g.opts

        Parameters:
            tymth is injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock is injected initial tock value

        Usage:
            add result of doify on this method to doers list
        """
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        while True:
            while self.cues:
                cue = self.cues.pull()  # self.cues.popleft()
                cueKin = cue["kin"]
                if cueKin == "stream":
                    self.queries.append(cue)
                else:
                    self.responses.append(cue)
                yield self.tock
            yield self.tock


class HttpEnd:
    """
    HTTP handler that accepts and KERI events POSTed as the body of a request with all attachments to
    the message as a CESR attachment HTTP header.  KEL Messages are processed and added to the database
    of the provided Habitat.

    This also handles `req`, `exn` and `tel` messages that respond with a KEL replay.
    """

    TimeoutQNF = 30
    TimeoutMBX = 5

    def __init__(self, rxbs=None, mbx=None, qrycues=None):
        """
        Create the KEL HTTP server from the Habitat with an optional Falcon App to
        register the routes with.

        Parameters
             rxbs (bytearray): output queue of bytes for message processing
             mbx (Mailboxer): Mailbox storage
             qrycues (Deck): inbound qry response queues

        """
        self.rxbs = rxbs if rxbs is not None else bytearray()

        self.mbx = mbx
        self.qrycues = qrycues if qrycues is not None else decking.Deck()

    def on_post(self, req, rep):
        """
        Handles POST for KERI event messages.

        Parameters:
              req (Request) Falcon HTTP request
              rep (Response) Falcon HTTP response

        ---
        summary:  Accept KERI events with attachment headers and parse
        description:  Accept KERI events with attachment headers and parse.
        tags:
           - Events
        requestBody:
           required: true
           content:
             application/json:
               schema:
                 type: object
                 description: KERI event message
        responses:
           200:
              description: Mailbox query response for server sent events
           204:
              description: KEL or EXN event accepted.
        """
        if req.method == "OPTIONS":
            rep.status = falcon.HTTP_200
            return

        rep.set_header('Cache-Control', "no-cache")
        rep.set_header('connection', "close")

        cr = httping.parseCesrHttpRequest(req=req)
        sadder = coring.Sadder(ked=cr.payload, kind=eventing.Kinds.json)
        msg = bytearray(sadder.raw)
        msg.extend(cr.attachments.encode("utf-8"))

        self.rxbs.extend(msg)

        if sadder.proto in ("ACDC",):
            rep.set_header('Content-Type', "application/json")
            rep.status = falcon.HTTP_204
        else:
            ilk = sadder.ked["t"]
            if ilk in (Ilks.icp, Ilks.rot, Ilks.ixn, Ilks.dip, Ilks.drt, Ilks.exn, Ilks.rpy):
                rep.set_header('Content-Type', "application/json")
                rep.status = falcon.HTTP_204
            elif ilk in (Ilks.vcp, Ilks.vrt, Ilks.iss, Ilks.rev, Ilks.bis, Ilks.brv):
                rep.set_header('Content-Type', "application/json")
                rep.status = falcon.HTTP_204
            elif ilk in (Ilks.qry,):
                if sadder.ked["r"] in ("mbx",):
                    rep.set_header('Content-Type', "text/event-stream")
                    rep.status = falcon.HTTP_200
                    rep.stream = QryRpyMailboxIterable(mbx=self.mbx, cues=self.qrycues, said=sadder.said)
                else:
                    rep.set_header('Content-Type', "application/json")
                    rep.status = falcon.HTTP_204

    def on_put(self, req, rep):
        """
        Handles PUT for KERI mbx event messages.

        Parameters:
              req (Request) Falcon HTTP request
              rep (Response) Falcon HTTP response

        ---
        summary:  Accept KERI events with attachment headers and parse
        description:  Accept KERI events with attachment headers and parse.
        tags:
           - Events
        requestBody:
           required: true
           content:
             application/json:
               schema:
                 type: object
                 description: KERI event message
        responses:
           200:
              description: Mailbox query response for server sent events
           204:
              description: KEL or EXN event accepted.
        """
        if req.method == "OPTIONS":
            rep.status = falcon.HTTP_200
            return

        rep.set_header('Cache-Control', "no-cache")
        rep.set_header('connection', "close")

        self.rxbs.extend(req.bounded_stream.read())

        rep.set_header('Content-Type', "application/json")
        rep.status = falcon.HTTP_204


class QryRpyMailboxIterable:

    def __init__(self, cues, mbx, said, retry=5000):
        self.mbx = mbx
        self.retry = retry
        self.cues = cues
        self.said = said
        self.iter = None

    def __iter__(self):
        return self

    def __next__(self):
        if self.iter is None:
            if self.cues:
                cue = self.cues.pull()
                serder = cue["serder"]
                if serder.said == self.said:
                    kin = cue["kin"]
                    if kin == "stream":
                        self.iter = iter(MailboxIterable(mbx=self.mbx, pre=cue["pre"], topics=cue["topics"],
                                                         retry=self.retry))
                else:
                    self.cues.append(cue)

            return b''

        return next(self.iter)


class MailboxIterable:
    TimeoutMBX = 30000000

    def __init__(self, mbx, pre, topics, retry=5000):
        self.mbx = mbx
        self.pre = pre
        self.topics = topics
        self.retry = retry

    def __iter__(self):
        self.start = self.end = time.perf_counter()
        return self

    def __next__(self):
        if self.end - self.start < self.TimeoutMBX:
            if self.start == self.end:
                self.end = time.perf_counter()
                return bytearray(f"retry: {self.retry}\n\n".encode("utf-8"))

            data = bytearray()
            for topic, idx in self.topics.items():
                key = self.pre + topic
                for fn, _, msg in self.mbx.cloneTopicIter(key, idx):
                    data.extend(bytearray("id: {}\nevent: {}\nretry: {}\ndata: ".format(fn, topic, self.retry)
                                          .encode("utf-8")))
                    data.extend(msg)
                    data.extend(b'\n\n')
                    idx = idx + 1
                    self.start = time.perf_counter()

                self.topics[topic] = idx
            self.end = time.perf_counter()
            return data

        raise StopIteration


class ReceiptEnd(doing.DoDoer):
    """ Endpoint class for Witnessing receipting functionality

     Most times a witness will be able to return its receipt for an event inband.  This API
     will provide that functionality.  When an event needs to be escrowed, this POST API
     will return a 202 and also provides a generic GET API for retrieving a receipt for any
     event.

     """

    def __init__(self, hab, inbound=None, outbound=None, aids=None):
        self.hab = hab
        self.inbound = inbound if inbound is not None else decking.Deck()
        self.outbound = outbound if outbound is not None else decking.Deck()
        self.aids = aids
        self.receipts = set()
        self.psr = parsing.Parser(framed=True,
                                  kvy=self.hab.kvy)

        super(ReceiptEnd, self).__init__(doers=[doing.doify(self.interceptDo)])

    def on_post(self, req, rep):
        """  Receipt POST endpoint handler

        Parameters:
            req (Request): Falcon HTTP request object
            rep (Response): Falcon HTTP response object

        """

        if req.method == "OPTIONS":
            rep.status = falcon.HTTP_200
            return

        rep.set_header('Cache-Control', "no-cache")
        rep.set_header('connection', "close")

        cr = httping.parseCesrHttpRequest(req=req)
        serder = serdering.SerderKERI(sad=cr.payload, kind=eventing.Kinds.json)

        pre = serder.ked["i"]
        if self.aids is not None and pre not in self.aids:
            raise falcon.HTTPBadRequest(description=f"invalid AID={pre} for witnessing receipting")

        ilk = serder.ked["t"]
        if ilk not in (Ilks.icp, Ilks.rot, Ilks.ixn, Ilks.dip, Ilks.drt):
            raise falcon.HTTPBadRequest(description=f"invalid event type ({ilk})for receipting")

        msg = bytearray(serder.raw)
        msg.extend(cr.attachments.encode("utf-8"))

        self.psr.parseOne(ims=msg, local=True)

        if pre in self.hab.kevers:
            kever = self.hab.kevers[pre]
            wits = kever.wits

            if self.hab.pre not in wits:
                raise falcon.HTTPBadRequest(description=f"{self.hab.pre} is not a valid witness for {pre} event at "
                                                        f"{serder.sn}: wits={wits}")

            rct = self.hab.receipt(serder)

            self.psr.parseOne(bytes(rct))

            rep.set_header('Content-Type', "application/json+cesr")
            rep.status = falcon.HTTP_200
            rep.data = rct
        else:
            rep.status = falcon.HTTP_202

    def on_get(self, req, rep):
        """  Receipt GET endpoint handler

        Parameters:
            req (Request): Falcon HTTP request object
            rep (Response): Falcon HTTP response object

        """
        pre = req.get_param("pre")
        sn = req.get_param_as_int("sn")
        said = req.get_param("said")

        if pre is None:
            raise falcon.HTTPBadRequest(description="query param 'pre' is required")

        preb = pre.encode("utf-8")

        if sn is None and said is None:
            raise falcon.HTTPBadRequest(description="either 'sn' or 'said' query param is required")

        if sn is not None:
            said = self.hab.db.getKeLast(key=dbing.snKey(pre=preb,
                                                         sn=sn))

        if said is None:
            raise falcon.HTTPNotFound(description=f"event for {pre} at {sn} ({said}) not found")

        said = bytes(said)
        dgkey = dbing.dgKey(preb, said)  # get message
        if not (raw := self.hab.db.getEvt(key=dgkey)):
            raise falcon.HTTPNotFound(description="Missing event for dig={}.".format(said))

        serder = serdering.SerderKERI(raw=bytes(raw))
        if serder.sn > 0:
            wits = [wit.qb64 for wit in self.hab.kvy.fetchWitnessState(pre, serder.sn)]
        else:
            wits = serder.ked["b"]

        if self.hab.pre not in wits:
            raise falcon.HTTPBadRequest(description=f"{self.hab.pre} is not a valid witness for {pre} event at "
                                                    f"{serder.sn}, {wits}")
        rserder = eventing.receipt(pre=pre,
                                   sn=sn,
                                   said=said.decode("utf-8"))
        rct = bytearray(rserder.raw)
        if wigs := self.hab.db.getWigs(key=dgkey):
            rct.extend(Counter(Codens.WitnessIdxSigs, count=len(wigs),
                               gvrsn=kering.Vrsn_1_0).qb64b)
            for wig in wigs:
                rct.extend(wig)

        rep.set_header('Content-Type', "application/json+cesr")
        rep.status = falcon.HTTP_200
        rep.data = rct

    def interceptDo(self, tymth=None, tock=0.0, **kwa):
        """
         Returns doifiable Doist compatibile generator method (doer dog) to process
            Kevery and Tevery cues deque

        Usage:
            add result of doify on this method to doers list
        """
        # enter context
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        while True:
            while self.inbound:  # iteratively process each cue in cues
                cue = self.inbound.popleft()
                cueKin = cue["kin"]  # type or kind of cue

                if cueKin in ("receipt",):  # cue to receipt a received event from other pre
                    serder = cue["serder"]  # Serder of received event for other pre
                    if serder.saidb in self.receipts:
                        self.receipts.remove(serder.saidb)
                    else:
                        self.outbound.append(cue)

                else:
                    self.outbound.append(cue)

                yield self.tock

            yield self.tock


class QueryEnd:
    """ Endpoint class for quering witness for KELs and TELs using HTTP GET

     """

    def __init__(self, hab):
        self.hab = hab
        self.reger = viring.Reger(name=hab.name, db=hab.db, temp=False)

    def on_get(self, req, rep):
        """ Handles GET requests to query KEL or TEL events of a pre from a witness.

            Parameters:
                req (Request) Falcon HTTP request
                rep (Response) Falcon HTTP response

            Query Parameters:
                typ (string): The type of event data to query for. Accepted values are:
                    - 'kel': Retrieve KEL events for a specified 'pre'.
                    - 'tel': Retrieve TEL events  based on 'reg' or 'vcid'.
                pre (string, optional): For 'kel' queries, the specific 'pre' to query.
                sn (int, optional): For "kel" queries. If provided, returns events with seq-num
                                   greater than or equal to `sn`.
                reg (string, optional): For 'tel' queries, registry pre. required if `vcid` is not provided.
                vcid (string, optional): For 'tel' queries, credential said. required if `reg` is not provided.

            Response:
                - 200 OK: Returns event data in "application/json+cesr" format.
                - 400 Bad Request: Returned if required query parameters are missing or if an invalid `typ` is specified.

            Example:
                - /query?typ=kel&pre=ELZ1KBCFOmdj1RPu6kMUnzgMBTl4YsHfpw7wIGvLgW5W
                - /query?typ=kel&pre=ELZ1KBCFOmdj1RPu6kMUnzgMBTl4YsHfpw7wIGvLgW5W&sn=5
                - /query?typ=tel&reg=EHrbPfpRLU9wpFXTzGY-LIo2FjMiljjEnt238eWHb7yZ&vcid=EO5y0jMXS5XKTYBKjCUPmNKPr1FWcWhtKwB2Go2ozvr0

        """

        typ = req.get_param("typ")

        if not typ:
            raise falcon.HTTPBadRequest(description="'typ' query param is required")

        if typ == "kel":
            pre = req.get_param("pre")

            if not pre:
                raise falcon.HTTPBadRequest(description="'pre' query param is required")

            evnts = bytearray()

            sn = req.get_param_as_int("sn")
            if sn is not None:  # query for event with seq-num >= sn
                preb = pre.encode("utf-8")
                dig = self.hab.db.getKeLast(key=dbing.snKey(pre=preb,
                                                         sn=sn))
                if dig is None:
                    raise falcon.HTTPBadRequest(description=f"non-existant event at seq-num {sn}")

                for dig in self.hab.db.getKelIter(pre, sn=sn):
                    try:
                        msg = self.hab.db.cloneEvtMsg(pre=pre, fn=0, dig=dig)
                    except Exception:
                        continue  # skip this event
                    evnts.extend(msg)
            else:
                for msg in self.hab.db.clonePreIter(pre=pre):
                    evnts.extend(msg)

            rep.set_header('Content-Type', "application/json+cesr")
            rep.status = falcon.HTTP_200
            rep.data = bytes(evnts)

        elif typ == "tel":
            regk = req.get_param("reg")
            vcid = req.get_param("vcid")

            if not regk and not vcid:
                raise falcon.HTTPBadRequest(description="Either 'reg' or 'vcid' query param is required for TEL query")

            evnts = bytearray()
            if regk is not None:
                cloner = self.reger.clonePreIter(pre=regk)
                for msg in cloner:
                    evnts.extend(msg)

            if vcid is not None:
                cloner = self.reger.clonePreIter(pre=vcid)
                for msg in cloner:
                    evnts.extend(msg)

            rep.set_header('Content-Type', "application/json+cesr")
            rep.status = falcon.HTTP_200
            rep.data = bytes(evnts)

        else:
            rep.set_header('Content-Type', "application/json")
            rep.text = "unkown query type."
            rep.status = falcon.HTTP_400
