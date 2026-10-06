from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///./data/itdesk.db')
with engine.connect() as conn:
    conn.execute(text('UPDATE tickets SET assigned_to_id = assigned_engineer_id WHERE assigned_to_id IS NULL'))
    conn.commit()
    print('Data copied')