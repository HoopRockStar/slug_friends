# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################
def index():
  return dict(form=auth())
  
@auth.requires_login()
def home():
  groups = db((db.Groups.id == db.Group_Members.group_id) \
      & (auth.user_id == db.Group_Members.member)).select()
  return dict(groups=groups, current_user=auth.user)

@auth.requires_login()
def profile():
  groups = db((db.Groups.id == db.Group_Members.group_id) \
      & (db.Group_Members.member == request.args[0])).select()
  profile_user = db(db.auth_user.id == request.args[0]).select().first()
  interests = db((db.Keywords.id == db.User_Interests.interest) \
      & (db.User_Interests.user == request.args[0])).select()
  return dict(groups=groups, profile_user=profile_user, interests=interests)
  
@auth.requires_login()  
def groups():
    db(db.Groups.id==db.Groups(request.args[0]))
    group = db.Groups(request.args[0]) or redirect(URL('index'))
    admin = db((db.Group_Members.member==db.auth_user.id) & (db.Group_Members.group_id==group.id)).select(db.Group_Members.administrator)
    member = db((db.Group_Members.group_id==db.Groups(request.args[0])) & (db.Group_Members.member==auth.user_id)).select()
    es = db(db.Events.group_id==group.id).select()
    session.group_id = group.id
    return dict(group=group, es=es, admin=admin, member=member, session=session, current_user=auth.user)
 
@auth.requires_login() 
def createAGroup():
    form=SQLFORM(db.Groups)
    if form.process().accepted:
        response.flash="Your group has been added"
        db.Group_Members.insert(group_id=form.vars.id, member=auth.user_id, administrator='True', rating=0)
        db.commit()
        redirect(URL('groups', args=[form.vars.id]))
    elif form.errors:
        response.flash="Please correct any errors"
    else:
        response.flash="Please enter the information for your group"
    return dict(form=form)

@auth.requires_login()         
def listGroups():
    groups = db().select(db.Groups.ALL)
    return dict(groups=groups)
     
@auth.requires_login() 
def displayEvent():
    group_member = db(db.Group_Members.member==auth.user_id).select(db.Group_Members.member)
    if not group_member:
        session.flash = T("You must be a member of this group to view events! ")
        redirect(URL('groups', args=[session.group_id]))
    db(db.Events.id==db.Events(request.args[0]))
    event = db.Events(request.args[0]) or redirect(URL('index'))
    session.event_id = event.id 
    c = db(db.Comments.event==event.id).select()
    attending = db(db.Attendees.attendee==auth.user_id).select()
    mem = db(db.auth_user.id==db.Comments.member).select(db.auth_user.username, db.auth_user.photo)    
    form = crud.create(db.Comments) if auth.user else None
    return dict(event=event, c=c, mem=mem, group_member=group_member, session=session, attending=attending, form=form, comments=db(db.Comments).select())

@auth.requires_login()
def joinGroup():
    db.Group_Members.insert(group_id=session.group_id, member=auth.user_id, rating=0)
    db.commit()
    session.flash = T('Welcome to the group! ')
    redirect(URL('groups', args=[session.group_id]))

@auth.requires_login()
def leaveGroup():
    db((db.Group_Members.member == auth.user_id) & (db.Group_Members.group_id==session.group_id)).delete()
    db.commit() 
    session.flash = T('You have left this group. We are sorry to see you go! ')
    redirect(URL('groups', args=[session.group_id]))

@auth.requires_login()         
def RSVP():
    db.Attendees.insert(event=session.event_id, attendee=auth.user_id)
    db.commit()
    db((db.Group_Members.member == auth.user_id) & (db.Group_Members.group_id==session.group_id)).update(rating = db.Group_Members.rating + 1)
    db.commit()
    session.flash = T('Your RSVP was successful. We look forward to seeing you there! ')
    redirect(URL('displayEvent', args=[session.event_id]))
    
@auth.requires_login()
def unRSVP():
    db((db.Attendees.attendee == auth.user_id) & (db.Attendees.event==session.event_id)).delete()
    db.commit()
    db((db.Group_Members.member == auth.user_id) & (db.Group_Members.group_id==session.group_id)).update(rating = db.Group_Members.rating - 1)
    db.commit()
    session.flash = T('You are no longer registered for this event! ')
    redirect(URL('displayEvent', args=[session.event_id]))

@auth.requires_login()      
def mycal():
    rows = db((db.Attendees.attendee==auth.user_id) &(db.Events.id==db.Attendees.event)).select(db.Events.ALL)  
    return dict(rows=rows)
   
def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request,db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())
