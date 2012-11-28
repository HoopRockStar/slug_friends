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
    )

db.define_table('Group_Members',
    Field('group_id', db.Groups),
    Field('member', db.auth_user, default=auth.user_id),
    Field('administrator', 'boolean', default='False'),
    Field('rating', 'integer', default=0),
    )

db.define_table('Events',
    Field('photo', 'upload'),
    Field('title', 'string', requires=IS_NOT_EMPTY()),
    Field('date', 'date', requires=IS_NOT_EMPTY()),
    Field('time', 'time', requires=IS_NOT_EMPTY()),
    Field('location', 'string', requires=IS_NOT_EMPTY()),
    Field('address','string'),
    Field('city','string'),
    Field('zipcode', 'integer'),
    Field('group_id', db.Groups),
    Field('description', 'text', requires=IS_NOT_EMPTY())
    )
               
db.define_table('Attendees',
    Field('event', db.Events),
    Field('attendee', db.auth_user, default=auth.user_id),
    Field('administrator', 'boolean', default='False'),
    )
   
db.define_table('Comments',
    Field('event', db.Events),
    Field('member', db.auth_user, default=auth.user_id),
    Field('posted_on','datetime',default=request.now),
    Field('comment', 'text', requires=IS_NOT_EMPTY()),
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
db.Comments.event.writable = db.Comments.event.readable = False
db.Comments.member.writable = db.Comments.member.readable = False
db.Comments.posted_on.writable = db.Comments.posted_on.readable = False
