# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
##SlugFriends
##Jennifer Parrish (HoopRockStar) served as group project manager.
##She designed the database, and developed the idea for this project.
##She created all code pertaining to groups
##including adding and deleting groups, appointing admins and
##stepping down as admin, creating and updating events, commenting on
##events, joining a group, (part of) listing members, removing and reinstating members
##different views for group members with different roles,
##She also adapted calendar code, created the logo, and designed layout for
##index page and homepage. 
##Dennis Foley (dmfoley23) coded (some of) the homepage, (all of) search and keyword and
##the user profile, (part of) listing group members, designed the SlugFriends word art
##Jesus Magana (zerolinux) was in charge of design, html and css
##Calendar adapted from Appointment Manager here: http://web2py.com/appliances
#########################################################################

@auth.requires_login()
def index():
  redirect(URL('home'))
  return dict()

#Homepage with links to recommended groups, calendar, starting a new group, searching for groups,
#viewing and editing profile, this week's events
@auth.requires_login()
def home():
  import datetime
  groupQ2 = (auth.user_id == db.Group_Members.member) 
  groupQ2 &= (db.Group_Members.group_id == db.Groups.id)
  exRows = db(groupQ2).select(db.Groups.ALL)
  a = []
  for exRow in exRows:
      a.append(exRow.id)
  groupQ1 = db.Groups.id == db.Search.group_id
  groupQ1 &= auth.user_id == db.User_Interests.user_id
  groupQ1 &= db.Search.keyword_id == db.User_Interests.interest
  groupQ1 &= ~db.Groups.id.belongs(a)
  groups = db(groupQ1).select(db.Groups.ALL, orderby='<random>', limitby=(0, 4))
  date_start = request.now.date()
  date_end = date_start + datetime.timedelta(days=7) 
  eventQ = db.Group_Members.member == auth.user_id
  eventQ &= db.Group_Members.group_id == db.Groups.id
  eventQ &= db.Events.group_id == db.Groups.id
  eventQ &= db.Events.date > date_start
  eventQ &= db.Events.date < date_end
  events = db(eventQ).select(db.Events.ALL,orderby=db.Events.date)
  form = SQLFORM.factory(Field('interest',));
  if form.process().accepted:
     if len(form.vars.interest) > 0:
         redirect(URL('search', args=[form.vars.interest]))
  count_groups = db((db.Group_Members.member==auth.user_id) & (db.Groups.id==db.Group_Members.group_id)).count() 
  count_interests = db((db.User_Interests.user_id==auth.user_id) & (db.User_Interests.interest==db.Keywords.id)).count()         
  return dict(form=form, groups=groups, current_user=auth.user, events=events, count_groups=count_groups, count_interests=count_interests)

#Search for a new group with your interests
def search():
  if len(request.args[0]) > 0:
     form = SQLFORM.factory(Field('interest',));
     rowid = db(db.Keywords.keyword == request.args[0]).select(db.Keywords.id).first()
     groups = db((db.Search.keyword_id == rowid)
           & (db.Search.group_id == db.Groups.id)).select(db.Groups.ALL)
     if form.process().accepted:
        if len(form.vars.interest) > 0:
           rowid = db(db.Keywords.keyword == form.vars.interest).select(db.Keywords.id).first()
           groups = db((db.Search.keyword_id == rowid)
              & (db.Search.group_id == db.Groups.id)).select(db.Groups.ALL)
  else:
      redirect(URL('home'))
  return dict(form=form, groups=groups)

#User profile information - username, photo, interests, group membership  
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
              INPUT(_name='image_file',_type='file', requires=IS_IMAGE()),
              INPUT(_value='submit', _type='submit'))
      groupQ1 = db.Group_Members.group_id == db.Groups.id
      groupQ1 &= db.Group_Members.member == request.args[0]
      groupQ1 &= db.Group_Members.administrator=="True"
      adminGroups = db(groupQ1).select(db.Groups.ALL)
  else:
      redirect(URL('home'));
  if form1.process(formname='form1').accepted:
      s = form1.vars.description
      db(db.auth_user.id==auth.user_id).update(description=s)
      db.commit()
      profile_user = db(db.auth_user.id == request.args[0]).select().first()
      form1 = SQLFORM.factory(Field('description', 'text', default=profile_user.description));
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
  return dict(groups=groups, adminGroups=adminGroups, profile_user=profile_user, interests=interests, form1=form1, form2=form2, form3=form3) 

def keys_complete():
    keys = db(db.Keywords.keyword.startswith(request.vars.term)).select(db.Keywords.keyword).as_list()
    word_list = [s['keyword'] for s in keys]
    import gluon.contrib.simplejson
    return gluon.contrib.simplejson.dumps(word_list) 
  
@auth.requires_login()  
def groups():
    import datetime
    db(db.Groups.id==db.Groups(request.args[0]))
    group = db.Groups(request.args[0]) or redirect(URL('index'))
    session.group_id = group.id
    session.group_name = group.name
    removed = db((db.Removed_Members.group_id==session.group_id) & (db.Removed_Members.member==auth.user_id)).select().first()
    if removed:
        session.flash = T("You have been removed from this group and are no longer permitted to participate in its activities! Please contact the group administrator with any questions ")
        redirect(URL('profile', args=[auth.user_id]))
    admin = db((db.Group_Members.group_id==session.group_id) & (db.Group_Members.member==auth.user_id) &
            (db.Group_Members.administrator=="True")).select(db.Group_Members.member).first()
    member = db((db.Group_Members.group_id==db.Groups(request.args[0])) & (db.Group_Members.member==auth.user_id)).select()
    active = db(db.Groups.id==session.group_id).select(db.Groups.active)
    date_start = request.now.date()
    date_end = date_start + datetime.timedelta(days=550)
    es = db((db.Events.group_id==group.id) & (db.Events.date > date_start) & (db.Events.date < date_end)).select(orderby=db.Events.date)
    
    interests = db((db.Keywords.id == db.Search.keyword_id) & (db.Search.group_id == group.id)).select(db.Keywords.ALL)
    return dict(group=group, es=es, admin=admin, member=member, session=session, current_user=auth.user, interests=interests, removed=removed, active=active)
 
#displays a list of members in the group including username and photo - displays different info depending on role
@auth.requires_login()
def viewMembers():
    group_member = db(db.Group_Members.member==auth.user_id).select(db.Group_Members.member)
    #handling non-members who wish to access the group info
    if not group_member:
        session.flash = T("You must be a member of this group to view other members! ")
        redirect(URL('groups', args=[session.group_id]))
    group = db(db.Groups.id==session.group_id).select(db.Groups.ALL)
    #current group members
    members = db((db.Group_Members.member==db.auth_user.id) & 
        (db.Group_Members.group_id==session.group_id)).select(db.auth_user.ALL, db.Group_Members.ALL, orderby=db.auth_user.username)
    q1 = (db.Group_Members.member==db.auth_user.id)
    q1 &= (db.Group_Members.group_id==session.group_id)
    q1 &= (db.Group_Members.administrator==True)
    #group administrator(s)
    admins = db(q1).select(db.auth_user.ALL)
    admin = db((db.Group_Members.group_id==session.group_id) & (db.Group_Members.member==auth.user_id) &
            (db.Group_Members.administrator=="True")).select(db.Group_Members.member).first()
    #members who have been removed from the group - only viewable by admin
    removed_members = db((db.Removed_Members.group_id==session.group_id) & 
        (db.auth_user.id==db.Removed_Members.member)).select(db.auth_user.ALL, orderby=db.auth_user.username)
    return dict(group=group, admins=admins, members=members, admin=admin, removed_members=removed_members)

#removes members from a group and inserts into Removed Members - must be group admin to access
@auth.requires_login()        
def removeMember():
   admin = db((db.Group_Members.group_id==session.group_id) & (db.Group_Members.member==auth.user_id) &
            (db.Group_Members.administrator=="True")).select(db.Group_Members.member).first()
   if not admin:
          session.flash = T('You must be a group administrator to remove members! ') 
          redirect(URL('viewMembers'))     
   db.Removed_Members.insert(group_id=session.group_id, member=request.args[0])
   db.commit()
   db((db.Group_Members.member==request.args[0]) & (db.Group_Members.group_id==session.group_id)).delete()
   db.commit()
   session.flash = T('This member has been removed from the group! ')
   redirect(URL('viewMembers'))   

#Reinstates members who have been removed from group - must be group admin to access
@auth.requires_login()        
def reinstateMember():
   admin = db((db.Group_Members.group_id==session.group_id) & (db.Group_Members.member==auth.user_id) &
        (db.Group_Members.administrator=="True")).select(db.Group_Members.member).first()
   if not admin:
       session.flash = T('You must be a group administrator to reinstate members! ') 
       redirect(URL('viewMembers')) 
   db.Group_Members.insert(group_id=session.group_id, member=request.args[0])
   db.commit()
   db((db.Removed_Members.member==request.args[0]) & (db.Removed_Members.group_id==session.group_id)).delete()
   db.commit()
   session.flash = T('This member has been reinstated to the group! ')
   redirect(URL('viewMembers'))             

#Apoints a new admin - only accessible by current administrator(s) 
@auth.requires_login()        
def makeAdmin():
    admin = db((db.Group_Members.group_id==session.group_id) & (db.Group_Members.member==auth.user_id) &
        (db.Group_Members.administrator=="True")).select(db.Group_Members.member).first()
    if not admin:
       session.flash = T('You must be a group administrator to appoint administrators! ') 
       redirect(URL('viewMembers'))     
    db((db.Group_Members.member==request.args[0]) & (db.Group_Members.group_id==session.group_id)).update(administrator='True')
    db.commit()
    session.flash = T('This member is now a group administrator! ')
    redirect(URL('viewMembers'))    

#Allows current admin to step down - must be another admin appointed to view this option (see view)            
@auth.requires_login()
def deleteAdmin():
    admin = db((db.Group_Members.group_id==session.group_id) & (db.Group_Members.member==auth.user_id) &
            (db.Group_Members.administrator=="True")).select(db.Group_Members.member).first()
    if not admin:
       session.flash = T('You must be a group administrator to access this functionality! ')
       redirect(URL('viewMembers'))
    count = db((db.Group_Members.group_id==session.group_id) &
            (db.Group_Members.administrator=="True")).count()      
    if (count == 1):
        session.flash=T("You must appoint a new administrator before you can step down.")
        redirect(URL('viewMembers'))
    form = SQLFORM.factory(Field('Confirm_deletion', 'boolean', default=False))
    if form.process().accepted:
        db((db.Group_Members.member==request.args[0]) & (db.Group_Members.group_id==session.group_id)).update(administrator='False')
        db.commit()
        session.flash = T('You are no longer a group administrator ')
        redirect(URL('viewMembers'))  
    return dict(form=form, user=auth.user)            

#For admin to edit group info
@auth.requires_login()
def editGroup():
    admin = db((db.Group_Members.group_id==session.group_id) & (db.Group_Members.member==auth.user_id) &
            (db.Group_Members.administrator=="True")).select(db.Group_Members.member).first()
    if not admin:
       session.flash = T('You must be a group administrator to access this functionality! ')
       redirect(URL('index'))    
    this_group = db.Groups(request.args(0,cast=int)) or redirect(URL('index'))
    form = crud.update(db.Groups, this_group, next=URL('groups',args=request.args))
    return dict(form=form) 

#Admin or even host to edit event info    
@auth.requires_login()
def editEvent():
    event_host=db((db.Attendees.event==session.event_id) & (db.Attendees.administrator=='True')).select(db.Attendees.attendee).first()
    admin = db((db.Group_Members.group_id==session.group_id) & (db.Group_Members.member==auth.user_id) &
            (db.Group_Members.administrator=="True")).select(db.Group_Members.member).first()
    if (not admin or not event_host):
       session.flash = T('You must be a group administrator to access this functionality! ')
       redirect(URL('index')) 
    this_event = db.Events(request.args(0,cast=int)) or redirect(URL('index'))
    form = crud.update(db.Events, this_event, next=URL('displayEvent',args=request.args))
    return dict(form=form, event_host=event_host, admin=admin)     

#Allows group admin to edit group keywords (search words defining group interests)    
@auth.requires_login()
def editGroupKeywords():
    group = db(db.Groups.id==request.args[0]).select().first() or redirect(URL('index'))
    form1 = SQLFORM.factory(Field('interest', requires=IS_NOT_EMPTY("interest can not be empty")));
    form2 = FORM(INPUT(_value='Finished', _type='submit'))
    interests = db((db.Keywords.id == db.Search.keyword_id) & (db.Search.group_id == group.id)).select()
    if form1.process(formname='form1').accepted:
       response.flash="Your group keyword has been added! "
       if db(db.Keywords.keyword==form1.vars.interest).select().first():
          rowid = db(db.Keywords.keyword==form1.vars.interest).select().first()
          if db((db.Search.keyword_id == rowid.id) 
                &(db.Search.group_id == group.id)).select().first():
              response.flash='interest already exists for this group';
          else:
              db.Search.insert(group_id=group.id, keyword_id=rowid.id)
              db.commit()
              interests = db((db.Keywords.id == db.Search.keyword_id)
                 & (db.Search.group_id == group.id)).select()
       else:
          db.Keywords.insert(keyword=form1.vars.interest)
          rowid = db(db.Keywords.keyword==form1.vars.interest).select(db.Keywords.id).first()
          db.Search.insert(group_id=group.id, keyword_id=rowid)
          db.commit()  
          interests = db((db.Keywords.id == db.Search.keyword_id)
             & (db.Search.group_id == group.id)).select()
    elif form1.errors:
        response.flash="Please correct any errors"   
    if form2.process(formname='form2').accepted:
        redirect(URL('groups', args=[group.id])) 
    return dict(form1=form1, form2=form2, group=group, interests=interests)  

#Allows admin to remove keywords
@auth.requires_login()
def deleteKeywords():    
    db((db.Search.group_id == session.group_id) & (db.Search.keyword_id == request.args[0])).delete()
    db.commit()
    session.flash = T('The keyword has been deleted ')
    redirect(URL('editGroupKeywords', args=[session.group_id]))      
 
#Allows user to delete listed interest(s)     
@auth.requires_login()
def deleteInterest():    
    if db((db.User_Interests.user_id == auth.user_id) & (db.User_Interests.interest == request.args[0])):
        db((db.User_Interests.user_id == auth.user_id) & (db.User_Interests.interest == request.args[0])).delete()
        db.commit()
        session.flash = T('The interest has been deleted ')
    redirect(URL('profile', args=[auth.user_id]))  

#Creates a new group        
@auth.requires_login() 
def createAGroup():    
    form=SQLFORM(db.Groups)
    if form.process().accepted:
        response.flash="Your group has been added"
        session.group_id = form.vars.id
        session.group_name = form.vars.name
        db.Group_Members.insert(group_id=form.vars.id, member=auth.user_id, administrator='True', rating=0)
        db(db.Groups.id == session.group_id).update(active = 'True')
        db.commit()
        db.commit()
        redirect(URL('groupKeywords', args=[form.vars.id]))
    elif form.errors:
        response.flash="Please correct any errors"
    else:
        response.flash="Please enter the information for your group"
    return dict(form=form, session=session)

#Create group keywords (search words for group interests) for new group
@auth.requires_login()            
def groupKeywords():
    group = db(db.Groups.id==request.args[0]).select().first() or redirect(URL('index'))
    form1 = SQLFORM.factory(Field('interest', requires=IS_NOT_EMPTY("interest can not be empty")));
    form2 = FORM(INPUT(_value='Finished', _type='submit'))
    interests = db((db.Keywords.id == db.Search.keyword_id) & (db.Search.group_id == group.id)).select()
    if form1.process(formname='form1').accepted:
       response.flash="Your group keyword has been added! "
       if db(db.Keywords.keyword==form1.vars.interest).select().first():
          rowid = db(db.Keywords.keyword==form1.vars.interest).select().first()
          if db((db.Search.keyword_id == rowid.id) 
                &(db.Search.group_id == group.id)).select().first():
              response.flash='The interest already exists for this group';
          else:
              db.Search.insert(group_id=group.id, keyword_id=rowid.id)
              db.commit()
              interests = db((db.Keywords.id == db.Search.keyword_id)
                 & (db.Search.group_id == group.id)).select()
       else:
          db.Keywords.insert(keyword=form1.vars.interest)
          rowid = db(db.Keywords.keyword==form1.vars.interest).select(db.Keywords.id).first()
          db.Search.insert(group_id=group.id, keyword_id=rowid)
          db.commit()  
          interests = db((db.Keywords.id == db.Search.keyword_id)
             & (db.Search.group_id == group.id)).select()
    elif form1.errors:
        response.flash="Please correct any errors"   
    if form2.process(formname='form2').accepted:
        redirect(URL('groups', args=[group.id])) 
    return dict(form1=form1, form2=form2, group=group, interests=interests)

#For debugging purposes - lists all groups on record                    
@auth.requires_login()         
def listGroups():
    groups = db().select(db.Groups.ALL)
    return dict(groups=groups)

#For debugging          
@auth.requires_login()            
def deleteGroups():     
    db(db.Groups.id==db.Groups(request.args[0])).delete()
    db.commit()
    redirect(URL('listGroups'))     

#Allows group member to create an event     
@auth.requires_login()
def createEvent():
    group_member = db(db.Group_Members.member==auth.user_id).select(db.Group_Members.member)
    if not group_member:
        session.flash = T("You must be a member of this group to view other members! ")
        redirect(URL('groups', args=[session.group_id]))    
    form = SQLFORM(db.Events)
    if form.process().accepted:
        response.flash="Your event has been added"
        db.commit()
        db(db.Events.id==form.vars.id).update(group_id=session.group_id)
        db.commit()
        db.Attendees.insert(event=form.vars.id, attendee=auth.user_id)
        db.commit()
        db(db.Attendees.attendee==auth.user_id).update(administrator='True')
        db.commit()
        redirect(URL('displayEvent', args=[form.vars.id]))
    elif form.errors:
        response.flash="Please correct any errors"
    else:
        response.flash="Please enter the information for your event"
    return dict(form=form)

#Displays event information including date/time/tile, description, attendees, comments         
@auth.requires_login() 
def displayEvent():
    group_member = db(db.Group_Members.member==auth.user_id).select(db.Group_Members.member)
    if not group_member:
        session.flash = T("You must be a member of this group to view events! ")
        redirect(URL('groups', args=[session.group_id]))
    db(db.Events.id==db.Events(request.args[0]))
    event = db.Events(request.args[0]) or redirect(URL('index'))
    session.event_id = event.id 
    comments = db(db.Comments.event_id==session.event_id).select()
    attending = db((db.Attendees.attendee == auth.user_id) & (db.Attendees.event==session.event_id)).select(db.Attendees.attendee)
    admin = db((db.Group_Members.group_id==session.group_id) & (db.Group_Members.member==auth.user_id) &
            (db.Group_Members.administrator=="True")).select(db.Group_Members.member).first()
    mem = db(db.auth_user.id==db.Comments.member).select(db.auth_user.username, db.auth_user.photo)  
    members_attending = db((db.Attendees.event == session.event_id) & (db.auth_user.id==db.Attendees.attendee)).select(db.auth_user.ALL)  
    event_host=db((db.Attendees.event==session.event_id) & (db.Attendees.administrator=='True')).select().first()
    #Generate new comments
    form = SQLFORM(db.Comments)
    if form.process().accepted:
        response.flash="Thank you for your comment! "
        db.commit()
        db(db.Comments.id==form.vars.id).update(event_id=session.event_id)
        db.commit()
        db(db.Comments.id==form.vars.id).update(author=auth.user_id)
        db.commit()
        redirect(URL('displayEvent', args=[session.event_id]))
    elif form.errors:
        response.flash="Please correct any errors"
        
    
    return dict(event=event, comments=comments, mem=mem, group_member=group_member, 
        session=session, attending=attending, form=form, admin=admin, members_attending=members_attending, event_host=event_host)

#Become member of a new group
@auth.requires_login()
def joinGroup():
    db.Group_Members.insert(group_id=session.group_id, member=auth.user_id, rating=0)
    db.commit()
    session.flash = T('Welcome to the group! ')
    redirect(URL('groups', args=[session.group_id]))

#Leave a current group
@auth.requires_login()
def leaveGroup():
    db((db.Group_Members.member == auth.user_id) & (db.Group_Members.group_id==session.group_id)).delete()
    db.commit() 
    session.flash = T('You have left this group. We are sorry to see you go! ')
    redirect(URL('groups', args=[session.group_id]))

#RSVP yes for a group event
@auth.requires_login()         
def RSVP():
    group_member = db(db.Group_Members.member==auth.user_id).select(db.Group_Members.member)
    if not group_member:
        session.flash = T("You must be a member of this group to RSVP for events! ")
        redirect(URL('groups', args=[session.group_id]))    
    db.Attendees.insert(event=session.event_id, attendee=auth.user_id)
    db.commit()
    db((db.Group_Members.member == auth.user_id) & 
    (db.Group_Members.group_id==session.group_id)).update(rating = db.Group_Members.rating + 1)
    db.commit()
    session.flash = T('Your RSVP was successful. We look forward to seeing you there! ')
    redirect(URL('displayEvent', args=[session.event_id]))

#RSVP no for a group event        
@auth.requires_login()
def unRSVP():
    db((db.Attendees.attendee == auth.user_id) & (db.Attendees.event==session.event_id)).delete()
    db.commit()
    db((db.Group_Members.member == auth.user_id) & (db.Group_Members.group_id==session.group_id)).update(rating = db.Group_Members.rating - 1)
    db.commit()
    session.flash = T('You are no longer registered for this event! ')
    redirect(URL('displayEvent', args=[session.event_id]))

#User personal SlugFriends calendar - events for groups user is a member of
@auth.requires_login()      
def mycal():
    rows = db((db.Attendees.attendee==auth.user_id) & (db.Events.id==db.Attendees.event)).select(db.Events.ALL)
    return dict(rows=rows)

#Delete a comment
@auth.requires_login()
def deleteComments():
    db(db.Comments.id == request.args[0]).delete()
    db.commit()
    session.flash = T('The comment has been deleted')
    redirect(URL('displayEvent', args=[session.event_id]))

#The following code for activating and inactivating a group is still under development        
@auth.requires_login()         
def activateGroup():
    db(db.Groups.id == session.group_id).update(active= 'True')
    db.commit()
    session.flash = T('This group is now active again!')
    redirect(URL('groups', args=[session.group_id]))   
    
@auth.requires_login()         
def inactivateGroup():
    db(db.Groups.id == session.group_id).update(active='False')
    db.commit()
    session.flash = T('This group is no longer active.')
    redirect(URL('groups', args=[session.group_id]))    

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
    groups = db().select(db.Groups.ALL, limitby=(2, 7))
    return dict(form=auth(), groups=groups)


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
