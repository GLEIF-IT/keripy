# -*- encoding: utf-8 -*-
"""
keri.app.agent.agenting module

Agent functionality for interacting with KERI witnesses.
"""
import random

from hio.base import doing
from hio.help import decking

from keri import help, kering
from keri.core import eventing, coring, serdering, indexing
from keri.db import dbing
from keri.kering import Roles
from keri.app import httping, forwarding
from keri.app.agenting import messenger, messengerFrom, schemes, HTTPMessenger

logger = help.ogler.getLogger()


class WitnessReceiptor(doing.DoDoer):
    """
    Sends messages to all current witnesses of given identifier (from hab) and waits
    for receipts from each of those witnesses and propagates those receipts to each
    of the other witnesses after receiving the complete set.

    Removes all Doers and exits as Done once all witnesses have been sent the entire
    receipt set.  Could be enhanced to have a `once` method that runs once and cleans up
    and an `all` method that runs and waits for more messages to receipt.

    """

    def __init__(self, hby, msgs=None, cues=None, force=False, auths=None, **kwa):
        """
        For the current event, gather the current set of witnesses, send the event,
        gather all receipts and send them to all other witnesses

        Parameters:
            hby (Habery): Habitat of the identifier to receipt witnesses
            msgs (Deck): incoming messages to publish to witnesses
            cues (Deck): outgoing cues of successful messages
            force (bool): True means to send witnesses all receipts even if we have a full compliment.

        """
        self.hby = hby
        self.force = force
        self.msgs = msgs if msgs is not None else decking.Deck()
        self.cues = cues if cues is not None else decking.Deck()
        self.auths = auths if auths is not None else dict()

        super(WitnessReceiptor, self).__init__(doers=[doing.doify(self.receiptDo)], **kwa)

    def receiptDo(self, tymth=None, tock=0.0, **kwa):
        """
        Returns doifiable Doist compatible generator method (doer dog)

        Usage:
            add result of doify on this method to doers list

        Parameters:
            tymth is injected function wrapper closure returned by .tymen() of
                Tymist instance. Calling tymth() returns associated Tymist .tyme.
            tock is injected initial tock value

        """
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        while True:
            while self.msgs:
                evt = self.msgs.popleft()
                pre = evt["pre"]

                if pre not in self.hby.habs:
                    continue

                hab = self.hby.habs[pre]

                sn = evt["sn"] if "sn" in evt else hab.kever.sner.num
                wits = hab.kever.wits

                if len(wits) == 0:
                    continue

                msg = hab.makeOwnEvent(sn=sn)
                ser = serdering.SerderKERI(raw=msg)

                dgkey = dbing.dgKey(ser.preb, ser.saidb)

                witers = []
                for wit in wits:
                    auth = self.auths[wit] if wit in self.auths else None
                    witer = messenger(hab, wit, auth=auth)
                    witers.append(witer)
                    self.extend([witer])

                # Check to see if we already have all the receipts we need for this event
                wigs = hab.db.getWigs(dgkey)
                completed = len(wigs) == len(wits)
                if len(wigs) != len(wits):  # We have all the receipts, skip
                    for idx, witer in enumerate(witers):
                        wit = wits[idx]

                        for dmsg in hab.db.cloneDelegation(hab.kever):
                            witer.msgs.append(bytearray(dmsg))

                        if ser.ked['t'] in (coring.Ilks.icp, coring.Ilks.dip) or \
                                "ba" in ser.ked and wit in ser.ked["ba"]:  # Newly added witness, must send full KEL to catch up
                            for fmsg in hab.db.clonePreIter(pre=pre):
                                witer.msgs.append(bytearray(fmsg))

                        witer.msgs.append(bytearray(msg))  # make a copy
                        _ = (yield self.tock)

                    while True:
                        wigs = hab.db.getWigs(dgkey)
                        if len(wigs) == len(wits):
                            break
                        _ = yield self.tock

                # If we started with all our recipts, exit unless told to force resubmit of all receipts
                if completed and not self.force:
                    self.cues.push(evt)
                    continue

                # generate all rct msgs to send to all witnesses
                awigers = [indexing.Siger(qb64b=bytes(wig)) for wig in wigs]

                # make sure all witnesses have fully receipted KERL and know about each other
                for witer in witers:
                    ewits = []
                    wigers = []
                    for i, wit in enumerate(wits):
                        if wit == witer.wit:
                            continue
                        ewits.append(wit)
                        wigers.append(awigers[i])

                    if len(wigers) == 0:
                        continue

                    rctMsg = bytearray()

                    # Now that the witnesses have not met each other, send them each other's receipts
                    if ser.ked['t'] in (coring.Ilks.icp, coring.Ilks.dip):  # introduce new witnesses
                        rctMsg.extend(schemes(self.hby.db, eids=ewits))
                    elif ser.ked['t'] in (coring.Ilks.rot, coring.Ilks.drt) and \
                            ("ba" in ser.ked and witer.wit in ser.ked["ba"]):  # Newly added witness, introduce to all
                        rctMsg.extend(schemes(self.hby.db, eids=ewits))

                    rserder = eventing.receipt(pre=ser.pre,
                                               sn=sn,
                                               said=ser.said)
                    rctMsg.extend(eventing.messagize(serder=rserder, wigers=wigers))

                    witer.msgs.append(rctMsg)
                    _ = (yield self.tock)

                while True:
                    done = True
                    for witer in witers:
                        if not witer.idle:
                            yield 1.0
                            done = False
                            break
                    if done:
                        break

                self.remove(witers)

                self.cues.push(evt)
                yield self.tock

            yield self.tock


class WitnessInquisitor(doing.DoDoer):
    """
    Sends messages to all current witnesses of given identifier (from hab) and waits
    for receipts from each of those witnesses and propagates those receipts to each
    of the other witnesses after receiving the complete set.

    Removes all Doers and exits as Done once all witnesses have been sent the entire
    receipt set.  Could be enhanced to have a `once` method that runs once and cleans up
    and an `all` method that runs and waits for more messages to receipt.

    """

    def __init__(self, hby, reger=None, msgs=None, klas=None, **kwa):
        """
        For all msgs, select a random witness from Habitat's current set of witnesses
        send the msg and process all responses (KEL replays, RCTs, etc)

        Parameters:
            hby (Habitat): Habitat of the identifier to use to identify witnesses
            msgs: is the message buffer to process and send to one random witness.

        """
        self.hby = hby
        self.reger = reger
        self.klas = klas if klas is not None else HTTPMessenger
        self.msgs = msgs if msgs is not None else decking.Deck()
        self.sent = decking.Deck()

        super(WitnessInquisitor, self).__init__(doers=[doing.doify(self.msgDo)], **kwa)

    def msgDo(self, tymth=None, tock=1.0, **opts):
        """
        Returns doifiable Doist compatible generator method (doer dog)

        Usage:
            add result of doify on this method to doers list
        """
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        while True:
            while not self.msgs:
                yield self.tock

            evt = self.msgs.popleft()
            pre = evt["pre"]
            target = evt["target"]
            src = evt["src"]
            r = evt["r"]
            q = evt["q"]
            wits = evt["wits"] if "wits" in evt else None

            if "hab" in evt:
                hab = evt["hab"]
            elif (hab := self.hby.habByPre(src)) is None:
                continue

            if not wits and pre not in self.hby.kevers:
                logger.error(f"must have KEL for identifier to query {pre}")
                continue

            if not wits:
                ends = hab.endsFor(pre=pre)
                if Roles.controller in ends:
                    end = ends[Roles.controller]
                elif Roles.agent in ends:
                    end = ends[Roles.agent]
                elif Roles.witness in ends:
                    end = ends[Roles.witness]
                else:
                    logger.error(f"unable query: can not find a valid role for {pre}")
                    continue

                if len(end.items()) == 0:
                    logger.error(f"must have endpoint to query for pre={pre}")
                    continue

                ctrl, locs = random.choice(list(end.items()))
                if len(locs.items()) == 0:
                    logger.error(f"must have location in endpoint to query for pre={pre}")
                    continue

                witer = messengerFrom(hab=hab, pre=ctrl, urls=locs)
            else:
                wit = random.choice(wits)
                witer = messenger(hab, wit)

            self.extend([witer])

            msg = hab.query(target, src=witer.wit, route=r, query=q)  # Query for remote pre Event

            kel = forwarding.introduce(hab, witer.wit)
            if kel:
                witer.msgs.append(bytearray(kel))

            witer.msgs.append(bytearray(msg))

            while not witer.sent:
                yield self.tock

            self.sent.append(witer.sent.popleft())

            yield self.tock

    def query(self, pre, r="logs", sn='0', fn='0', src=None, hab=None, anchor=None, wits=None, **kwa):
        """ Create, sign and return a `qry` message against the attester for the prefix

        Parameters:
            src (str): qb64 identifier prefix of source of query
            hab (Hab): Hab to use instead of src if provided
            pre (str): qb64 identifier prefix being queried for
            r (str): query route
            sn (str): optional specific hex str of sequence number to query for
            fn (str): optional specific hex str of sequence number to start with
            anchor (Seal): anchored Seal to search for
            wits (list) witnesses to query

        Returns:
            bytearray: signed query event

        """
        qry = dict(s=sn, fn=fn)
        if anchor is not None:
            qry["a"] = anchor

        msg = dict(src=src, pre=pre, target=pre, r=r, q=qry, wits=wits)
        if hab is not None:
            msg["hab"] = hab

        self.msgs.append(msg)

    def telquery(self, ri, src=None, i=None, r="tels", hab=None, pre=None, wits=None, **kwa):
        qry = dict(ri=ri)
        msg = dict(src=src, pre=pre, target=i, r=r, wits=wits, q=qry)
        if hab is not None:
            msg["hab"] = hab

        self.msgs.append(msg)


class WitnessPublisher(doing.DoDoer):
    """
    Sends messages to all current witnesses of given identifier (from hab) and exits.

    Removes all Doers and exits as Done once all witnesses have been sent the message.
    Could be enhanced to have a `once` method that runs once and cleans up
    and an `all` method that runs and waits for more messages to receipt.

    """

    def __init__(self, hby, msgs=None, cues=None, **kwa):
        """
        For the current event, gather the current set of witnesses, send the event,
        gather all receipts and send them to all other witnesses

        Parameters:
            hby (Habery): Habitat of the identifier to populate witnesses
            msgs (Deck): incoming messages to publish to witnesses
            cues (Deck): outgoing cues of successful messages

        """
        self.hby = hby
        self.posted = 0
        self.msgs = msgs if msgs is not None else decking.Deck()
        self.cues = cues if cues is not None else decking.Deck()
        super(WitnessPublisher, self).__init__(doers=[doing.doify(self.sendDo)], **kwa)

    def sendDo(self, tymth=None, tock=0.0, **opts):
        """
        Returns doifiable Doist compatible generator method (doer dog)

        Usage:
            add result of doify on this method to doers list
        """
        self.wind(tymth)
        self.tock = tock
        _ = (yield self.tock)

        while True:
            while self.msgs:
                evt = self.msgs.popleft()
                self.posted += 1
                pre = evt["pre"]
                msg = evt["msg"]

                if pre not in self.hby.habs:
                    continue

                hab = self.hby.habs[pre]
                wits = hab.kever.wits

                witers = []
                for wit in wits:
                    witer = messenger(hab, wit)
                    witers.append(witer)
                    witer.msgs.append(bytearray(msg))  # make a copy so everyone munges their own
                    self.extend([witer])

                    _ = (yield self.tock)

                while witers:
                    witer = witers.pop()
                    while not witer.idle:
                        _ = (yield self.tock)

                self.remove(witers)
                self.cues.push(evt)

                yield self.tock

            yield self.tock

    def sent(self, said):
        """ Check if message with given SAID was sent

        Parameters:
            said (str): qb64 SAID of message to check for
        """

        for cue in self.cues:
            if cue["said"] == said:
                return True

        return False

    @property
    def idle(self):
        return len(self.msgs) == 0 and self.posted == len(self.cues)
