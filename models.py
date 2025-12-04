class User:
    def __init__(self, userid, username, password, email, reedzbalance, role, createdat):
        self.userid = userid
        self.username = username
        self.password = password
        self.email = email
        self.reedzbalance = reedzbalance
        self.role = role
        self.createdat = createdat

class Prediction:
    def __init__(self, predictionid, userid, betid, prediction, createdat):
        self.predictionid = predictionid
        self.userid = userid
        self.betid = betid
        self.prediction = prediction
        self.createdat = createdat

class Bet:
    def __init__(
        self,
        betid,
        createdbyuserid,
        title,
        description,
        answertype,
        isopen,
        isresolved,
        createdat,
        closeat,
        resolvedat=None,
        correctanswer=None,
        is_closed=False,
    ):
        self.betid = betid
        self.createdbyuserid = createdbyuserid
        self.title = title
        self.description = description
        self.answertype = answertype
        self.isopen = isopen
        self.isresolved = isresolved
        self.createdat = createdat
        self.closeat = closeat
        self.resolvedat = resolvedat
        self.correctanswer = correctanswer
        self.is_closed = is_closed
