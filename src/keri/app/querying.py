# -*- encoding: utf-8 -*-
"""
keri.app.storing module

"""
from dataclasses import dataclass

from hio.base import doing
from keri.app import agenting
from keri.db import dbing


@dataclass(frozen=True)
class KelTarget:
    """An accepted KEL position, optionally pinned to an exact event digest."""

    pre: str
    sn: int
    said: str | None = None

    def __post_init__(self):
        if not isinstance(self.sn, int) or self.sn < 0:
            raise ValueError("KEL target sequence number must be a nonnegative integer")

    def satisfied(self, hby, reger=None):
        kever = hby.kevers.get(self.pre)
        if kever is None or kever.sn < self.sn:
            return False
        dig = hby.db.getKeLast(dbing.snKey(self.pre, self.sn))
        return dig is not None and (self.said is None or bytes(dig).decode() == self.said)


@dataclass(frozen=True)
class AnchorTarget:
    """An exact event seal in an accepted, fully witnessed anchoring event."""

    pre: str
    seal: dict

    def satisfied(self, hby, reger=None):
        return hby.db.fetchLastSealingEventByEventSeal(self.pre, seal=self.seal) is not None


@dataclass(frozen=True)
class KeyStateTarget:
    """A saved notice from a specific source for an exact known state.

    This is a pinned-state check, not a claim that a cached notice is fresh or
    that the source has no newer state. Discovering 'latest' needs a separate
    freshness policy before constructing this target.
    """

    pre: str
    source: str
    sn: int
    said: str

    def __post_init__(self):
        if not isinstance(self.sn, int) or self.sn < 0:
            raise ValueError("key-state target sequence number must be a nonnegative integer")

    def satisfied(self, hby, reger=None):
        saider = hby.db.knas.get(keys=(self.pre, self.source))
        if saider is None:
            return False
        state = hby.db.ksns.get(keys=(saider.qb64,))
        return (state is not None and state.i == self.pre and
                int(state.s, 16) == self.sn and state.d == self.said)


@dataclass(frozen=True)
class TelTarget:
    """An exact event in the verified TEL index, after anchor validation."""

    pre: str
    sn: int
    said: str

    def __post_init__(self):
        if not isinstance(self.sn, int) or self.sn < 0:
            raise ValueError("TEL target sequence number must be a nonnegative integer")

    def satisfied(self, hby, reger=None):
        if reger is None:
            raise ValueError("TEL completion requires a Reger")
        dig = reger.getTel(dbing.snKey(self.pre, self.sn))
        return dig is not None and bytes(dig).decode() == self.said


class QueryDoer(doing.DoDoer):

    def __init__(self, hby, hab, kvy, pre, **kwa):
        self.hby = hby
        self.hab = hab
        self.kvy = kvy
        self.pre = pre

        doers = [KeyStateNoticer(hby=hby, hab=self.hab, pre=pre, cues=kvy.cues)]
        super(QueryDoer, self).__init__(doers=doers, **kwa)


class KeyStateNoticer(doing.DoDoer):

    def __init__(self, hby, hab, pre, cues, **opts):
        self.hby = hby
        self.hab = hab
        self.pre = pre
        self.cues = cues
        self.witq = agenting.WitnessInquisitor(hby=self.hby)
        self.witq.query(src=self.hab.pre, pre=self.pre, r="ksn")

        super(KeyStateNoticer, self).__init__(doers=[self.witq], **opts)

    def recur(self, tyme, deeds=None):
        if self.pre in self.hby.kevers:
            kever = self.hby.kevers[self.pre]
        else:
            return super(KeyStateNoticer, self).recur(tyme, deeds)

        if self.cues:
            cue = self.cues.pull()
            match cue['kin']:
                case "keyStateSaved":
                    kcue = cue
                    ksn = kcue['ksn']  # key state notice dict
                    match ksn["i"]:
                        case self.pre:
                            if kever.sn < int(ksn["s"], 16):
                                # Add new doer here instead of cueing to a while loop
                                self.extend([LogQuerier(hby=self.hby, hab=self.hab, ksn=ksn)])
                                self.remove([self.witq])

                            else:
                                return True

                        case _:
                            self.cues.append(cue)

                case _:
                    self.cues.append(cue)

        return super(KeyStateNoticer, self).recur(tyme, deeds)


class LogQuerier(doing.DoDoer):

    def __init__(self, hby, hab, ksn, **opts):
        self.hby = hby
        self.hab = hab
        self.ksn = ksn
        self.witq = agenting.WitnessInquisitor(hby=self.hby)
        self.target = KelTarget(self.ksn["i"], int(self.ksn["s"], 16), self.ksn["d"])
        self.witq.query(src=self.hab.pre, pre=self.ksn["i"], completion=self.target)
        super(LogQuerier, self).__init__(doers=[self.witq], **opts)

    def recur(self, tyme, deeds=None):
        """
        Returns:  doifiable Doist compatible generator method
        Usage:
            add result of doify on this method to doers list
        """
        if self.target.satisfied(self.hby):
            self.remove([self.witq])
            return True

        return super(LogQuerier, self).recur(tyme, deeds)


class SeqNoQuerier(doing.DoDoer):

    def __init__(self, hby, hab, pre, sn, fn=None, wits=None, **opts):
        self.hby = hby
        self.hab = hab
        self.pre = pre
        self.sn = sn
        self.fn = fn if fn is not None else 0
        self.witq = agenting.WitnessInquisitor(hby=self.hby)
        self.target = KelTarget(self.pre, self.sn)
        self.witq.query(src=self.hab.pre, pre=self.pre,
                        completion=self.target, sn="{:x}".format(self.sn),
                        fn="{:x}".format(self.fn),
                        wits=wits)
        super(SeqNoQuerier, self).__init__(doers=[self.witq], **opts)

    def recur(self, tyme, deeds=None):
        """
        Returns:  doifiable Doist compatible generator method
        Usage:
            add result of doify on this method to doers list
        """
        if self.pre not in self.hab.kevers:
            return False

        if self.target.satisfied(self.hby):
            self.remove([self.witq])
            return True

        return super(SeqNoQuerier, self).recur(tyme, deeds)


class AnchorQuerier(doing.DoDoer):

    def __init__(self, hby, hab, pre, anchor, **opts):
        self.hby = hby
        self.hab = hab
        self.pre = pre
        self.anchor = anchor
        self.witq = agenting.WitnessInquisitor(hby=self.hby)
        self.target = AnchorTarget(self.pre, anchor)
        self.witq.query(src=self.hab.pre, pre=self.pre, anchor=anchor, completion=self.target)
        super(AnchorQuerier, self).__init__(doers=[self.witq], **opts)

    def recur(self, tyme, deeds=None):
        """
        Returns:  doifiable Doist compatible generator method
        Usage:
            add result of doify on this method to doers list
        """
        if self.pre not in self.hab.kevers:
            return False

        if self.target.satisfied(self.hby):
            self.remove([self.witq])
            return True

        return super(AnchorQuerier, self).recur(tyme, deeds)
