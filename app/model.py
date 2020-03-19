#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 17 17:29:47 2020

@author: lucadelu
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

regionsuser = db.Table('regionsuser',
    db.Column('region_id', db.Integer, db.ForeignKey('region.id'),
              primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'),
              primary_key=True)
)

class Region(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slugname = db.Column(db.String(100), unique=True, nullable=False)
    
    def __repr__(self):
        return '<Region %r>' % self.name

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    regions = db.relationship('Region', secondary=regionsuser, lazy='subquery',
                              backref=db.backref('regions', lazy=True))
    
    def __repr__(self):
        return '<Email %r>' % self.email

def insert_user(email, slugregion):
    """Function to insert or update an email connected to a region
    
    :param str email: the email address to add/modify
    :param str slugregion: the slugfied name of the region
    """
    exists = User.query.filter_by(email=email).first()
    reg = Region.query.filter_by(slugname=slugregion).first()
    if exists:
        out = "È stato aggiornato l'utente {us} aggiungendo la regione {re}".format(
              us=email, re=reg.name)
        exists.regions.append(reg)
    else:
        new = User(email=email)
        new.regions.append(reg)
        db.session.add(new)
        out = "È stato creato il nuovo utente {us} aggiungendo la regione {re}".format(
              us=email, re=reg.name)
    db.session.commit()
    return out

def delete_user(email):
    """Delete an email address
    
    :param str email: the email address to remove
    """
    exists = User.query.filter_by(email=email).first()
    if exists:
        exists.regions = []
        db.session.commit()
        db.session.delete(exists)
        db.session.commit()
        out = "È stato eliminato l'utente {us}".format(us=email)
    else:
        out = "L'utente {us} non esiste".format(us=email)
    return out

def delete_user_region(email, slugregion, delete=True):
    """Delete a region for a email

    :param str email: the email address to consider
    :param str slugregion: the slugfied name of the region
    :param bool delete: delete completely the user if it has no region anymore
    """
    reg = Region.query.filter_by(slugname=slugregion).first()
    exists = User.query.filter_by(email=email).first()
    if exists:
        exists.regions.remove(reg)
        db.session.commit()
        exists = User.query.filter_by(email=email).first()
        if len(exists.regions) == 0 and delete:
            db.session.delete(exists)
            db.session.commit()
            out = "È stato eliminato l'utente {us} poichè non aveva più " \
                  "nessuna regione di interesse".format(us=email)
        else:
            out = "È stata eliminata la region {re} dall'utente {us}".format(re=reg.name,
                                                                             us=email)
    else:
        out = "L'utente {us} non esiste".format(us=email)
    return out


def select_users(slugregion):
    """Function to return all user for a region
    
    :param str slugregion: the slugfied name of the region
    """
    reg = Region.query.filter_by(slugname=slugregion).first()
    users = User.query.with_entities(User.email).with_parent(reg,
                                                             'regions').all()
    return [value for value, in users]
