# coding: utf8

#db.define_table('Users',
#    Field('id', db.auth_user),
#    Field('name', 'string'),
#    Field('username', 'string'),
#    Field('photo', 'upload'),
#    Field('email', 'string'),
#    Field('password', 'password'),
#    Field('description', 'text'),
#    )
    
db.define_table('Groups',
    Field('photo', 'upload', requires=IS_NOT_EMPTY()),
    Field('name', 'string', requires=IS_NOT_EMPTY()),
    Field('description', 'text', requires=IS_NOT_EMPTY()),
    Field('active', 'boolean', default='True'),
    )

db.define_table('Group_Members',
    Field('group_id', db.Groups),
    Field('member', db.auth_user, default=auth.user_id),
    Field('administrator', 'boolean', default='False'),
    Field('rating', 'integer', default=0),
    )

db.define_table('Removed_Members',
    Field('member', db.auth_user, default=auth.user_id),
    Field('group_id', db.Groups),
    )
    
db.define_table('Events',
    Field('photo', 'upload', requires=IS_NOT_EMPTY()),
    Field('title', 'string', requires=IS_NOT_EMPTY()),
    Field('date', 'date', requires=IS_NOT_EMPTY()),
    Field('time', 'time', requires=IS_NOT_EMPTY()),
    Field('location', 'string', requires=IS_NOT_EMPTY()),
    Field('group_id', db.Groups, requires=IS_NOT_EMPTY()),
    Field('description', 'text', requires=IS_NOT_EMPTY()),
    )
               
db.define_table('Attendees',
    Field('event', db.Events),
    Field('attendee', db.auth_user, default=auth.user_id),
    Field('administrator', 'boolean', default='False'),
    )
   
db.define_table('Comments',
    Field('event_id', db.Events),
    Field('member', db.auth_user, default=auth.user_id),
    Field('posted_on','datetime',default=request.now),
    Field('comment', 'text', requires=IS_NOT_EMPTY()),
    Field('author',  db.auth_user, default=auth.user_id),
    )
       
db.define_table('Keywords',
    Field('keyword', 'string'),
    )

db.define_table('User_Interests',
    Field('user_id', db.auth_user, default=auth.user_id),
    Field('interest', db.Keywords),
    )
   
db.define_table('Search',
    Field('keyword_id', db.Keywords),
    Field('group_id', db.Groups),
    )

db.User_Interests.user_id.requires = IS_IN_DB(db,'auth_user.id', '%(first_name)s %(last_name)s', multiple=False)
#db.Users.email.requires = [IS_EMAIL(), IS_NOT_IN_DB(db, 'Users.email')]
db.Comments.event_id.writable = db.Comments.event_id.readable = False
db.Comments.member.writable = db.Comments.member.readable = False
db.Comments.posted_on.writable = db.Comments.posted_on.readable = False
db.Events.group_id.writable = db.Events.group_id.readable = False
db.Comments.author.writable = db.Comments.author.readable = False
db.Events.date.requires = IS_DATE(format=T('%Y-%m-%d'), error_message='must be YYYY-MM-DD!')
db.Events.time.requires = IS_TIME(error_message='must be HH:MM am/pm!')
db.Groups.photo.requires = IS_IMAGE()
db.Events.photo.requires = IS_IMAGE()
db.Groups.active.writable = db.Groups.active.readable = False
