# -*- coding: utf-8 -*-
# Copyright (c) 2025, Aakvatech and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.query_builder import DocType


def before_login(login_manager):
    """
    Validate if user is already logged in from another session.
    This function prevents multiple simultaneous logins using the same credentials.
    
    The system automatically expires sessions after inactivity (typically 5 minutes).
    This function simply checks if any active session exists for the user.
    
    Args:
        login_manager: The login manager object containing user information
    """
    user = login_manager.user
    
    # Skip validation for Administrator to avoid lockouts
    if user == "Administrator":
        return
    
    # Check for any active sessions for this user
    # The system automatically handles session expiration based on inactivity
    Sessions = DocType("Sessions")
    active_sessions = (
        frappe.qb.from_(Sessions)
        .select(Sessions.sid, Sessions.user, Sessions.lastupdate)
        .where(Sessions.user == user)
    ).run(as_dict=True)
    
    # If there are active sessions, prevent login
    if active_sessions:
        # Clear the current login attempt
        frappe.local.login_manager = None
        
        frappe.throw(
            msg=_(
                "You are already logged in from another device or browser."
                "<br><br><b>Please logout from your previous session before logging in again. </b>"
            ),
            title=_("<h4 class='text-danger font-bold'>Multiple Login Detected</h4>"),
        )

