import hunterprice as hp
import model

db_session = model.defaut_session()
application = hp.create_api(db_session)
