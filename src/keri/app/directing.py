# -*- encoding: utf-8 -*-
"""
KERI
keri.app.directing module

simple direct mode demo support classes
"""
import itertools
from hio import hioing
from hio.base import doing

from .. import help, kering
from ..core import eventing, routing
from ..core import parsing
from ..vdr.eventing import Tevery

logger = help.ogler.getLogger()


class Director(doing.Doer):
    """
    Base class for Direct Mode KERI Controller Doer with habitat and TCP Client

    Attributes:
        hab (Habitat: local controller's context
        client (serving.Client): hio TCP client instance.
            Assumes operated by another doer.

    Inherited Properties:
        tyme (float): relative cycle time of associated Tymist, obtained
            via injected .tymth function wrapper closure.
        tymth (function): function wrapper closure returned by Tymist .tymeth()
            method.  When .tymth is called it returns associated Tymist .tyme.
            .tymth provides injected dependency on Tymist tyme base.
        tock (float): desired time in seconds between runs or until next run,
            non negative, zero means run asap

    Properties:

    Inherited Methods:
        .__call__ makes instance callable return generator
        .do is generator function returns generator

    Methods:

    Hidden:
       ._tymth is injected function wrapper closure returned by .tymen() of
            associated Tymist instance that returns Tymist .tyme. when called.
       ._tock is hidden attribute for .tock property
    """

    def __init__(self, hab, client, **kwa):
        """
        Initialize instance.

        Inherited Parameters:
            tymist is  Tymist instance
            tock is float seconds initial value of .tock

        Parameters:
            hab is Habitat instance
            client is TCP Client instance. Assumes opened/closed elsewhere

        """
        super(Director, self).__init__(**kwa)
        self.hab = hab
        self.client = client  # use client to initiate comms
        if self.tymth:
            self.client.wind(self.tymth)

    def wind(self, tymth):
        """
        Inject new tymist.tymth as new ._tymth. Changes tymist.tyme base.
        Updates winds .tymer .tymth
        """
        super(Director, self).wind(tymth)
        self.client.wind(tymth)

    def sendOwnEvent(self, sn):
        """
        Utility to send own event at sequence number sn
        """
        msg = self.hab.makeOwnEvent(sn=sn)
        # send to connected remote
        self.client.tx(msg)
        logger.info("%s: %s sent event:\n%s\n\n", self.hab.name, self.hab.pre, bytes(msg))

    def sendOwnInception(self):
        """
        Utility to send own inception on client
        """
        self.sendOwnEvent(sn=0)


class Reactor(doing.DoDoer):
    """
    Reactor Subclass of DoDoer with doers list from do generator methods:
        .msgDo, .cueDo, and  .escrowDo.
    Enables continuous scheduling of doers (do generator instances or functions)

    Implements Doist like functionality to allow nested scheduling of doers.
    Each DoDoer runs a list of doers like a Doist but using the tyme from its
       injected tymist as injected by its parent DoDoer or Doist.

    Scheduling hierarchy: Doist->DoDoer...->DoDoer->Doers

    Inherited Attributes:
        .done is Boolean completion state:
            True means completed
            Otherwise incomplete. Incompletion maybe due to close or abort.
        .opts is dict of injected options for its generator .do
        .doers is list of Doers or Doer like generator functions

    Attributes:
        .hab is Habitat instance of local controller's context
        .client is TCP Client instance.
        .kevery is Kevery instance


    Inherited Properties:
        .tyme is float relative cycle time of associated Tymist .tyme obtained
            via injected .tymth function wrapper closure.
        .tymth is function wrapper closure returned by Tymist .tymeth() method.
            When .tymth is called it returns associated Tymist .tyme.
            .tymth provides injected dependency on Tymist tyme base.
        .tock is float, desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Properties:

    Inherited Methods:
        .wind  injects ._tymth dependency from associated Tymist to get its .tyme
        .__call__ makes instance callable
            Appears as generator function that returns generator
        .do is generator method that returns generator
        .enter is enter context action method
        .recur is recur context action method or generator method
        .clean is clean context action method
        .exit is exit context method
        .close is close context method
        .abort is abort context method

    Overidden Methods:

    Hidden:
       ._tymth is injected function wrapper closure returned by .tymen() of
            associated Tymist instance that returns Tymist .tyme. when called.
       ._tock is hidden attribute for .tock property

    """

    def __init__(self, hab, client, verifier=None, exchanger=None, direct=True, doers=None, **kwa):
        """
        Initialize instance.

        Inherited Parameters:
            tymist is  Tymist instance
            tock is float seconds initial value of .tock
            doers is list of doers (do generator instances, functions or methods)

        Parameters:
            hab is Habitat instance of local controller's context
            client is TCP Client instance
            verifier is Verifier instance of local controller's TEL context
            direct is Boolean, True means direct mode so process cue'd receipts
                    False means indirect mode so don't process cue'ed receipts

        """
        self.hab = hab
        self.client = client  # use client for both rx and tx
        self.verifier = verifier
        self.exc = exchanger
        self.direct = True if direct else False
        doers = doers if doers is not None else []
        doers.extend([doing.doify(self.msgDo, tock=hab.tocks["reactorMsg"]),
                      doing.doify(self.escrowDo, tock=hab.tocks["reactorEscrow"]),
                      doing.doify(self.cueDo, tock=hab.tocks["reactorCue"])])

        self.kevery = eventing.Kevery(db=self.hab.db,
                                      lax=False,
                                      local=False,
                                      direct=self.direct)

        if self.verifier is not None:
            self.tvy = Tevery(reger=self.verifier.reger,
                              db=self.hab.db,
                              local=False)
        else:
            self.tvy = None

        self.parser = parsing.Parser(ims=self.client.rxbs,
                                     framed=True,
                                     kvy=self.kevery,
                                     tvy=self.tvy,
                                     exc=self.exc)


        super(Reactor, self).__init__(doers=doers, **kwa)
        if self.tymth:
            self.client.wind(self.tymth)

    def wind(self, tymth):
        """
        Inject new tymist.tymth as new ._tymth. Changes tymist.tyme base.
        Updates winds .tymer .tymth
        """
        super(Reactor, self).wind(tymth)
        self.client.wind(tymth)


    def msgDo(self, tymth=None, tock=0.0, **opts):
        """
        Returns doifiable Doist compatibile generator method (doer dog) to process
            incoming message stream of .kevery

        Doist Injected Attributes:
            g.tock = tock  # default tock attributes
            g.done = None  # default done state
            g.opts

        Parameters:
            tymth is injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock is injected initial tock value
            opts is dict of injected optional additional parameters


        Usage:
            add result of doify on this method to doers list
        """
        self.wind(tymth)
        _ = (yield tock)  # enter context
        if self.parser.ims:
            logger.info("Client %s received:\n%s\n...\n", self.hab.name, self.parser.ims[:1024])
        parser = self.parser.parsator(local=True)
        while True:
            try:
                next(parser)
            except StopIteration as ex:
                return ex.value  # should never get here except forced close
            yield tock


    def cueDo(self, tymth=None, tock=0.0, **opts):
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
            opts is dict of injected optional additional parameters

        Usage:
            add result of doify on this method to doers list
        """
        self.wind(tymth)
        _ = (yield tock)  # enter context
        while True:
            for msg in self.hab.processCuesIter(self.kevery.cues):
                self.sendMessage(msg, label="chit or receipt")
                yield tock  # throttle just do one cue at a time
            yield tock
        return False  # should never get here except forced close

    def escrowDo(self, tymth=None, tock=0.0, **opts):
        """
         Returns doifiable Doist compatibile generator method (doer dog) to process
            .kevery escrows.

        Doist Injected Attributes:
            g.tock = tock  # default tock attributes
            g.done = None  # default done state
            g.opts

        Parameters:
            tymth is injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock is injected initial tock value
            opts is dict of injected optional additional parameters

        Usage:
            add result of doify on this method to doers list
        """
        self.wind(tymth)
        _ = (yield tock)  # enter context
        while True:
            self.kevery.processEscrows()
            if self.tvy is not None:
                self.tvy.processEscrows()
            yield tock
        return False  # should never get here except forced close

    def sendMessage(self, msg, label=""):
        """
        Sends message msg and loggers label if any
        """
        try:
            self.client.tx(msg)  # Queue locally; admission is not delivery.
        except hioing.TransmitClosedError as ex:
            # rc3 rejects new output after terminal send; keep the scheduler alive
            # and account for bytes that never entered the transport buffer.
            error = self.client.error if self.client.error is not None else ex
            logger.error("Client %s could not queue %s after transmit cutoff; "
                         "rejected=%d: %s", self.hab.name, label, len(msg), error)
            return
        logger.info("%s sent %s:\n%s\n\n", self.hab.name, label, bytes(msg))


class Directant(doing.DoDoer):
    """
    Directant class with TCP Server.
    Responds to initiated connections from a remote Director by creating and
    running a Reactant per connection. Each Reactant has TCP remoter.

    Receive cutoff starts a bounded drain of accepted input and generated
    responses. Teardown waits for parser, response producer and transmit buffer
    settlement, or records terminal send failure/deadline expiry. This is local
    settlement, not proof of peer processing or durable storage.

    Directant Subclass of DoDoer with doers list from do generator methods:
        .serviceDo

    Enables continuous scheduling of doers (do generator instances or functions)

    Implements Doist like functionality to allow nested scheduling of doers.
    Each DoDoer runs a list of doers like a Doist but using the tyme from its
       injected tymist as injected by its parent DoDoer or Doist.

    Scheduling hierarchy: Doist->DoDoer...->DoDoer->Doers

    Inherited Attributes:
        .done is Boolean completion state:
            True means completed
            Otherwise incomplete. Incompletion maybe due to close or abort.
        .opts is dict of injected options for its generator .do
        .doers is list of Doers or Doer like generator functions

    Attributes:
        .hab is Habitat instance of local controller's context
        .server is TCP client instance. Assumes operated by another doer.
        .rants is dict of Reactants indexed by connection address
        .drainTymeout is finite positive whole-drain duration, independent of idle timeout
        .drainStops maps connection addresses to absolute, non-refreshing deadlines

    Inherited Properties:
        .tyme is float relative cycle time of associated Tymist .tyme obtained
            via injected .tymth function wrapper closure.
        .tymth is function wrapper closure returned by Tymist .tymeth() method.
            When .tymth is called it returns associated Tymist .tyme.
            .tymth provides injected dependency on Tymist tyme base.
        .tock is desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Properties:

    Inherited Methods:
        .wind  injects ._tymth dependency from associated Tymist to get its .tyme
        .__call__ makes instance callable
            Appears as generator function that returns generator
        .do is generator method that returns generator
        .enter is enter context action method
        .recur is recur context action method or generator method
        .clean is clean context action method
        .exit is exit context method
        .close is close context method
        .abort is abort context method

    Methods:

    Hidden:
       ._tymth is injected function wrapper closure returned by .tymen() of
            associated Tymist instance that returns Tymist .tyme. when called.
       ._tock is hidden attribute for .tock property
    """

    DrainTymeout = 30.0  # force TCP teardown, bounding application and transmit drain after receive EOF

    def __init__(self, hab, server, verifier=None, exchanger=None, doers=None,
                 drainTymeout=None, **kwa):
        """
        Initialize instance.

        Inherited Parameters:
            tymist is  Tymist instance
            tock is float seconds initial value of .tock

        Parameters:
            db is database instance of local controller's context
            verifier (optional) is Verifier instance of local controller's TEL context
            server is TCP Server instance
            drainTymeout is finite positive whole-drain duration; defaults to 30 seconds
        """
        self.hab = hab
        self.verifier = verifier
        self.exchanger = exchanger
        self.server = server  # use server for cx
        self.rants = dict()
        self.drainTymeout = (float(drainTymeout) if drainTymeout is not None
                             else self.DrainTymeout)
        if not 0.0 < self.drainTymeout < float("inf"):
            raise ValueError("drainTymeout must be finite and positive")
        self.drainStops = dict()
        doers = doers if doers is not None else []
        doers.extend([doing.doify(self.serviceDo)])
        super(Directant, self).__init__(doers=doers, **kwa)
        if self.tymth:
            self.server.wind(self.tymth)

    def wind(self, tymth):
        """
        Inject new tymist.tymth as new ._tymth. Changes tymist.tyme base.
        Updates winds .tymer .tymth
        """
        super(Directant, self).wind(tymth)
        self.server.wind(tymth)


    def serviceDo(self, tymth=None, tock=0.0, **opts):
        """
        Returns doifiable Doist compatibile generator method (doer dog) to service
            connections on .server. Creates remoter and rant (Reactant) for each
            open connection and adds rant to running doers.

        Doist Injected Attributes:
            g.tock = tock  # default tock attributes
            g.done = None  # default done state
            g.opts

        Parameters:
            tymth is injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock is injected initial tock value
            opts is dict of injected optional additional parameters


        Usage:
            add result of doify on this method to doers list
        """
        yield  # enter context
        while True:
            for ca, ix in list(self.server.ixes.items()):
                if not ix.cutoff:
                    if ix.txCutoff:
                        # Sending cannot recover, but pending input still deserves parsing.
                        ix.serviceReceives()
                        ix.shutdownReceive()
                    elif ix.tymeout > 0.0 and ix.tymer.expired:
                        # Boundary input may refresh the idle timer before local shutdown.
                        ix.serviceReceives()
                        if not ix.cutoff and ix.tymer.expired:
                            ix.shutdownReceive()

                # Local receive shutdown uses the same bounded drain as peer EOF.
                # Without input or a Reactant, no application work owns this connection.
                if ca not in self.rants and ix.cutoff and not ix.rxbs:
                    if ix.txbs:
                        reason = ("transmit cutoff" if ix.txCutoff else
                                  "queued output without Reactant")
                        self._logDrainFailure(ca=ca, ix=ix, reason=reason)
                    self.closeConnection(ca)
                    continue

                # One deadline bounds the whole drain; send activity must not extend it.
                if ix.cutoff and ca not in self.drainStops:
                    self.drainStops[ca] = self.tyme + self.drainTymeout

                # Buffered input still needs a parser when EOF arrived before creation.
                if ca not in self.rants:  # create Reactant and extend doers with it
                    rant = Reactant(tymth=self.tymth, hab=self.hab, verifier=self.verifier,
                                    exchanger=self.exchanger, remoter=ix)
                    self.rants[ca] = rant
                    # add Reactant (rant) doer to running doers
                    self.extend(doers=[rant])  # open and run rant as doer

                if ix.cutoff:
                    rant = self.rants[ca]
                    rxSettled = rant.rxDrained or rant.rxFailed
                    # Parsed input may still owe responses or have bytes queued for sending.
                    outputDrained = rant.responseSettled and not ix.txbs
                    deadlineExpired = self.tyme >= self.drainStops[ca]

                    if rxSettled and outputDrained:
                        self.closeConnection(ca)
                    elif rxSettled and ix.txCutoff:
                        self._logDrainFailure(ca=ca, ix=ix, rant=rant,
                                              reason="transmit cutoff")
                        self.closeConnection(ca)
                    elif deadlineExpired:
                        self._logDrainFailure(ca=ca, ix=ix, rant=rant,
                                              reason="drain deadline expired")
                        self.closeConnection(ca)

            yield

    @staticmethod
    def _logDrainFailure(ca, ix, reason, rant=None):
        """Log application and transport work abandoned by terminal close.

        Parameters:
            ca: Connection address used by ``server.ixes``.
            ix: Remoter whose accepted or queued bytes are being abandoned.
            reason: Stable human-readable terminal close reason.
            rant: Optional Reactant containing parser and producer state.
        """
        logger.error("Closing direct connection %s after %s; "
                     "rxbs=%d, messageInProgress=%s, responseSettled=%s, "
                     "txbs=%d, txCutoff=%s",
                     ca,
                     reason,
                     len(ix.rxbs),
                     rant.messageInProgress if rant is not None else False,
                     rant.responseSettled if rant is not None else True,
                     len(ix.txbs),
                     ix.txCutoff)

    def closeConnection(self, ca):
        """
        Close and remove connection given by ca and remove associated rant at ca.
        """
        # Sending belongs to server service; removal must not attempt an untracked send.
        if ca in self.server.ixes:  # remoter still there
            self.server.removeIx(ca)
        if ca in self.rants:  # remove rant (Reactant) if any
            self.remove([self.rants[ca]])  # close and remove rant from doers list
            del self.rants[ca]
        self.drainStops.pop(ca, None)


class Reactant(doing.DoDoer):
    """
    Reactant Subclass of DoDoer with doers list from do generator methods:
        .msgDo, .cueDo, and .escrowDo.
    Enables continuous scheduling of doers (do generator instances or functions)

    Implements Doist like functionality to allow nested scheduling of doers.
    Each DoDoer runs a list of doers like a Doist but using the tyme from its
       injected tymist as injected by its parent DoDoer or Doist.

    Scheduling hierarchy: Doist->DoDoer...->DoDoer->Doers

    Attributes:
        .hab is Habitat instance of local controller's context
        .kevery is Kevery instance
        .remoter is TCP Remoter instance for connection from remote TCP client.

    Inherited Attributes:
        .done is Boolean completion state:
            True means completed
            Otherwise incomplete. Incompletion maybe due to close or abort.
        .opts is dict of injected options for its generator .do
        .doers is list of Doers or Doer like generator functions


    Inherited Properties:
        .tyme is float relative cycle time of associated Tymist .tyme obtained
            via injected .tymth function wrapper closure.
        .tymth is function wrapper closure returned by Tymist .tymeth() method.
            When .tymth is called it returns associated Tymist .tyme.
            .tymth provides injected dependency on Tymist tyme base.
        .tock is float, desired time in seconds between runs or until next run,
                 non negative, zero means run asap

    Properties:

    Inherited Methods:
        .wind  injects ._tymth dependency from associated Tymist to get its .tyme
        .__call__ makes instance callable
            Appears as generator function that returns generator
        .do is generator method that returns generator
        .enter is enter context action method
        .recur is recur context action method or generator method
        .clean is clean context action method
        .exit is exit context method
        .close is close context method
        .abort is abort context method

    Overidden Methods:

    Hidden:
       ._tymth is injected function wrapper closure returned by .tymen() of
            associated Tymist instance that returns Tymist .tyme. when called.
       ._tock is hidden attribute for .tock property

    """

    def __init__(self, hab, remoter, verifier=None, exchanger=None, doers=None, **kwa):
        """
        Initialize instance.

        Inherited Parameters:
            tymist is  Tymist instance
            tock is float seconds initial value of .tock
            doers is list of doers (do generator instancs or functions)

        Parameters:
            hby is Habitat instance of local controller's context
            verifier is Verifier instance of local controller's TEL context
            remoter is TCP Remoter instance
            doers is list of doers (do generator instances, functions or methods)

        """
        self.hab = hab
        self.verifier = verifier
        self.exchanger = exchanger
        self.remoter = remoter  # use remoter for both rx and tx
        self.messageInProgress = False
        self.cueInProgress = False
        self.rxError = None

        doers = doers if doers is not None else []
        doers.extend([doing.doify(self.msgDo, tock=hab.tocks["reactantMsg"]),
                      doing.doify(self.cueDo, tock=hab.tocks["reactantCue"]),
                      doing.doify(self.escrowDo, tock=hab.tocks["reactantEscrow"])])

        #  needs unique kevery with ims per remoter connnection
        rvy = routing.Revery(db=hab.db)
        self.kevery = eventing.Kevery(db=self.hab.db,
                                      lax=False,
                                      local=False,
                                      rvy=rvy)

        if self.verifier is not None:
            self.tevery = Tevery(reger=self.verifier.reger,
                                 db=self.hab.db,
                                 local=False, rvy=rvy)
            self.tevery.registerReplyRoutes(router=rvy.rtr)
        else:
            self.tevery = None

        self.kevery.registerReplyRoutes(router=rvy.rtr)

        self.parser = parsing.Parser(ims=self.remoter.rxbs,
                                     framed=True,
                                     kvy=self.kevery,
                                     tvy=self.tevery,
                                     exc=self.exchanger,
                                     rvy=rvy)

        super(Reactant, self).__init__(doers=doers, **kwa)
        if self.tymth:
            self.remoter.wind(self.tymth)

    def wind(self, tymth):
        """
        Inject new tymist.tymth as new ._tymth. Changes tymist.tyme base.
        Updates winds .tymer .tymth
        """
        super(Reactant, self).wind(tymth)
        self.remoter.wind(tymth)


    def msgDo(self, tymth=None, tock=0.0, **opts):
        """
        Returns doifiable Doist compatibile generator method (doer dog) to process
            incoming message stream of .kevery

        Doist Injected Attributes:
            g.tock = tock  # default tock attributes
            g.done = None  # default done state
            g.opts

        Parameters:
            tymth is injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock is injected initial tock value
            opts is dict of injected optional additional parameters


        Usage:
            add result of doify on this method to doers list
        """
        self.wind(tymth)
        _ = (yield tock)  # enter context
        # Keep serving successive messages while tracking each message separately.
        while True:
            while not self.parser.ims:
                yield tock

            logger.info("Server %s: received:\n%s\n...\n", self.hab.name,
                        self.parser.ims[:1024])
            # Unlike the continuous parsator, onceParsator exposes a message boundary.
            # Track partial messages even when parsing has emptied the receive buffer.
            messageParser = self.parser.onceParsator(local=True)
            self.messageInProgress = True
            try:
                # Resume the same message until it finishes or EOF prevents more input.
                while True:
                    try:
                        next(messageParser)
                    except StopIteration:
                        # This message ended, including any error handled by the parser.
                        break

                    # A yield needs more input; receive cutoff means none can arrive.
                    if self.remoter.cutoff:
                        remaining = len(self.parser.ims)
                        self.rxError = kering.ShortageError(
                            f"incomplete CESR message at EOF from "
                            f"{self.remoter.ca}; {remaining} buffered bytes remain")
                        del self.parser.ims[:]
                        logger.error(str(self.rxError))
                        break

                    yield tock
            finally:
                # Release the parser on completion, incomplete EOF, or doer cancellation.
                messageParser.close()
                self.messageInProgress = False

            yield tock

    @property
    def rxDrained(self):
        """Whether parsing is at a successful empty message boundary.

        True requires no receiver error, no message in progress, and no bytes
        in ``parser.ims``. This is terminal only after receive closure; an open
        idle connection may receive more.
        """
        return self.rxError is None and not self.messageInProgress and not self.parser.ims

    @property
    def rxFailed(self):
        """Whether receive closure exposed an incomplete CESR message."""
        return self.rxError is not None

    @property
    def responseSettled(self):
        """Whether queued and active response production is locally settled."""
        return not self.cueInProgress and not self.kevery.cues

    def cueDo(self, tymth=None, tock=0.0, **opts):
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
            opts is dict of injected optional additional parameters

        Usage:
            add result of doify on this method to doers list
        """
        self.wind(tymth)
        _ = (yield tock)  # enter context
        while True:
            # processCuesIter permits multiple messages per cue; the deque can
            # be empty while its suspended iterator still owes a response.
            self.cueInProgress = bool(self.kevery.cues)
            try:
                for msg in self.hab.processCuesIter(self.kevery.cues):
                    if isinstance(msg, list):
                        msg = bytearray(itertools.chain(*msg))

                    self.sendMessage(msg, label="chit or receipt or replay")
                    yield tock  # throttle just do one cue at a time
            finally:
                self.cueInProgress = False
            yield tock
        return False  # should never get here except forced close


    def escrowDo(self, tymth=None, tock=0.0, **opts):
        """
         Returns doifiable Doist compatibile generator method (doer dog) to process
            .kevery escrows.

        Doist Injected Attributes:
            g.tock = tock  # default tock attributes
            g.done = None  # default done state
            g.opts

        Parameters:
            tymth is injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock is injected initial tock value
            opts is dict of injected optional additional parameters

        Usage:
            add result of doify on this method to doers list
        """
        self.wind(tymth)
        _ = (yield tock)  # enter context
        while True:
            self.kevery.processEscrows()
            if self.tevery is not None:
                self.tevery.processEscrows()
            yield tock
        return False  # should never get here except forced close

    def sendMessage(self, msg, label=""):
        """
        Sends message msg and loggers label if any
        """
        try:
            self.remoter.tx(msg)  # Queue locally; admission is not delivery.
        except hioing.TransmitClosedError as ex:
            # rc3 rejects new output after terminal send; keep the scheduler alive
            # and account for bytes that never entered the transport buffer.
            error = self.remoter.error if self.remoter.error is not None else ex
            logger.error("Server %s could not queue %s after transmit cutoff; "
                         "rejected=%d: %s", self.hab.name, label, len(msg), error)
            return
        logger.info("Server %s: sent %s:\n%d\n\n", self.hab.name,
                    label, len(msg))


def runController(doers, expire=0.0):
    """
    Utiitity Function to create doist to run doers
    """
    tock = 0.03125
    doist = doing.Doist(limit=expire, tock=tock, real=True)
    doist.do(doers=doers)
