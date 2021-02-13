#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 19 22:18:37 2019

@author: lucadelu
"""
import os
import configparser
from caiosm.data_from_overpass import CaiOsmRouteDiff
from caiosm.functions import send_mail
import telegram


class ManageChanges:
    def __init__(
        self,
        area=None,
        sourceref=None,
        startdate=None,
        enddate=None,
        daydiff=1,
        path=None,
    ):
        """
        params str area: area to query
        params str sourceref: sezione code
        """
        if sourceref and area:
            raise ValueError("Please select only 'area' or 'sourceref'")
        if sourceref:
            self.cord = CaiOsmRouteDiff(
                sourceref=sourceref, enddate=enddate, startdate=startdate
            )
            self.title = "Aggiornamento dati per la sezione {}\n\n".format()
        elif area:
            self.cord = CaiOsmRouteDiff(area=area, startdate=startdate, enddate=enddate)
            self.title = "Aggiornamento dati per {}\n\n".format(area)
        else:
            raise ValueError("Please select one between 'area' or 'sourceref'")
        self.changes = self.cord.get_changeset()
        if not self.changes:
            return None
        self.text = self._set_text()
        self.config = configparser.ConfigParser()
        self.path = path
        if self.path:
            self.config.read(os.path.join(self.path, "cai_scripts.ini"))
        elif os.path.exists(os.path.join(os.path.expanduser("~"),
                                         "cai_scripts.ini")):
            self.config.read(os.path.join(os.path.expanduser("~"),
                                          "cai_scripts.ini"))

    def _set_text(self):
        """Prepare text for message"""
        if len(self.changes) == 1:
            outext = "C'è stato 1"
        elif len(self.changes) > 1:
            outext = "Ci sono stati {nc}".format(nc=len(self.changes))
        outext += (
            " changeset tra {sta} e {end} con modifiche che ti "
            "interessano:\n\n".format(sta=self.cord.startdate, end=self.cord.enddate)
        )
        for c in self.changes:
            outext += "* https://overpass-api.de/achavi/?changeset={idc}\n".format(
                idc=c
            )

        return self.title + outext

    def mail(self, bccs=None, ccs=None, path=None):
        """Function to send mail with new changeset

        :params list bccs: a list of mails to send in bcc
        :params list ccs: a list of mails to send in cc
        :params str path: the path to the ini file
        """
        if not path:
            path = self.path
        if not bccs and not ccs:
            raise Exception("Uno tra i campi ccs e bccs dev'essere popolato")
        send_mail(
            sub="Aggiornamento dai CAI in OSM",
            mess=self.text,
            bcc=bccs,
            cc=ccs,
            path=path,
        )

    def telegram(self, token=None, chatid=None):
        """Function to telegram update with new changeset

        :params str token: the token of the bot to use
        """
        if not token:
            token = self.config["TELEGRAM"]["token"]
        if not chatid:
            chatid = self.config["TELEGRAM"]["chatid"]
        bot = telegram.Bot(token=token)
        bot.send_message(chat_id=chatid, text=self.text)
        return True
