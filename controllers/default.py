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
  groupQ1 = db.Groups.id == db.Search.group_id
  groupQ1 &= auth.user_id == db.User_Interests.user_id
  groupQ1 &= db.Search.keyword_id == db.User_Interests.interest
  groupQ2 = (auth.user_id == db.Group_Members.member) 
  groupQ2 &= (db.Group_Members.group_id == db.Groups.id)
  groups = db(groupQ1).select(db.Groups.ALL, limitby=(0, 6)).exclude(db(groupQ2))
  events = db(db.Events.group_id == db.Groups.id).select(db.Events.ALL, orderby=db.Events.date, limitby=(0, 7))
  return dict(groups=groups, current_user=auth.user, events=events)

@auth.requires_login()
def profile():
  if(len(request.args) > 0):
      profile_user = db(db.auth_user.id == request.args[0]).select().first() or redirect(URL('index'))
      groups = db((db.Groups.id == db.Group_Members.group_id)
          & (db.Group_Members.member == request.args[0])).select()
      interests = db((db.Keywords.id == db.User_Interests.interest)
          & (db.User_Interests.user_id == request.args[0])).select()
      form1 = SQLFORM.factory(Field('description', 'text', default=profile_user.description));
      form2 = SQLFORM.factory(Field('interest', requires=IS_NOT_EMPTY("interest can not be empty")));
      form3 = FORM(INPUT(_name='image_title',_type='hidden', _value=auth.user_id),
              INPUT(_name='image_file',_type='file'),
              INPUT(_value='submit', _type='submit'))
  else:
      redirect(URL('home'));
  if form1.process(formname='form1').accepted:
      s = form1.vars.description
      db(db.auth_user.id==auth.user_id).update(description=s)
      db.commit()
      profile_user = db(db.auth_user.id == request.args[0]).select().first()
  if form2.process(formname='form2').accepted:
      if db(db.Keywords.keyword==form2.vars.interest).select().first():
          rowid = db(db.Keywords.keyword==form2.vars.interest).select().first()
          if db((db.User_Interests.interest == rowid.id) 
                &(db.User_Interests.user_id == profile_user.id)).select().first():
              response.flash='interest already exists for this user';
          else:
              db.User_Interests.insert(user_id=auth.user_id, interest=rowid.id)
              db.commit()
              interests = db((db.Keywords.id == db.User_Interests.interest)
                 & (db.User_Interests.user_id == request.args[0])).select()
      else:
          db.Keywords.insert(keyword=form2.vars.interest)
          rowid = db(db.Keywords.keyword==form2.vars.interest).select(db.Keywords.id).first()
          db.User_Interests.insert(user_id=auth.user_id, interest=rowid)
          db.commit()  
          interests = db((db.Keywords.id == db.User_Interests.interest)
             & (db.User_Interests.user_id == request.args[0])).select()
  if form3.process(formname='form3').accepted:
      image = db.auth_user.photo.store(form3.vars.image_file.file, form3.vars.image_file.filename)
      db(db.auth_user.id==auth.user_id).update(photo=image)
      db.commit()
      profile_user = db(db.auth_user.id == request.args[0]).select().first()
  return dict(groups=groups, profile_user=profile_user, interests=interests, form1=form1, form2=form2, form3=form3) 

def keys_complete():
    keys = db(db.Keywords.keyword.startswith(request.vars.term)).select(db.Keywords.keyword).as_list()
    word_list = [s['keyword'] for s in keys]
    import gluon.contrib.simplejson
    return gluon.contrib.simplejson.dumps(word_list) 
  
@auth.requires_login()  
def groups():
    db(db.Groups.id==db.Groups(request.args[0]))
    group = db.Groups(request.args[0]) or redirect(URL('index'))
    admin = db((db.Group_Members.member==auth.user_id) & 
        (db.Group_Members.group_id==group.id)).select(db.Group_Members.administrator)
    member = db((db.Group_Members.group_id==db.Groups(request.args[0])) & (db.Group_Members.member==auth.user_id)).select()
    es = db(db.Events.group_id==group.id).select()
    interests = db((db.Keywords.id == db.Search.keyword_id)
       & (db.Search.group_id == group.id)).select()
    session.group_id = group.id
    form = SQLFORM.factory(Field('interest', requires=IS_NOT_EMPTY("interest can not be empty")));
    if form.process(formname='form').accepted:
      if db(db.Keywords.keyword==form.vars.interest).select().first():
          rowid = db(db.Keywords.keyword==form.vars.interest).select().first()
          if db((db.Search.keyword_id == rowid.id)
               &(db.Search.group_id == group.id)).select().first():
              response.flash='interest already exists for this group';
          else:
              db.Search.insert(group_id=group.id, keyword_id=rowid.id)
              db.commit()
              interests = db((db.Keywords.id == db.Search.group_id)
                 & (db.Search.group_id == group.id)).select()
      else:
          db.Keywords.insert(keyword=form.vars.interest)
          rowid = db(db.Keywords.keyword==form.vars.interest).select(db.Keywords.id).first()
          db.Search.insert(group_id=group.id, keyword_id=rowid)
          db.commit()
          interests = db((db.Keywords.id == db.Search.keyword_id)
             & (db.Search.group_id == group.id)).select()
    return dict(group=group, es=es, admin=admin, member=member, 
        session=session, current_user=auth.user, form=form, interests=interests)
 
@auth.requires_login()
def viewMembers():
   if(len(request.args) > 0):
      group = db.Groups(request.args[0]) or redirect(URL('index'))
      members = db((db.Group_Members.member==db.auth_user.id) & 
          (db.Group_Members.group_id==group.id)).select(db.auth_user.ALL)
      q1 = (db.Group_Members.member==db.auth_user.id)
      q1 &= (db.Group_Members.group_id==group.id)
      q1 &= (db.Group_Members.administrator==True)
      admins = db(q1).select(db.auth_user.ALL)
   else:
      redirect(URL('home'));
   return dict(group=group, admins=admins, members=members)
   
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
    return dict(event=event, c=c, mem=mem, group_member=group_member, 
        session=session, attending=attending, form=form, comments=db(db.Comments).select())

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
    db((db.Group_Members.member == auth.user_id) & 
    (db.Group_Members.group_id==session.group_id)).update(rating = db.Group_Members.rating + 1)
    db.commit()
    session.flash = T('Your RSVP was successful. We look forward to seeing you there! ')
    redirect(URL('displayEvent', args=[session.event_id]))
    
@auth.requires_login()
def unRSVP():
    db((db.Attendees.attendee == auth.user_id) & (db.Attendees.event==session.event_id)).delete()
    db.commit()
    db((db.Group_Members.member == auth.user_id) & 
    (db.Group_Members.group_id==session.group_id)).update(rating = db.Group_Members.rating - 1)
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
