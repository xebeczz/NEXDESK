from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///./data/itdesk.db')
with engine.connect() as conn:
    conn.execute(text('DROP INDEX IF EXISTS ix_tickets_assigned_engineer_id'))
    conn.commit()
    print('Index dropped')