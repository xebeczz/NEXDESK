from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///./data/itdesk.db')
with engine.connect() as conn:
    conn.execute(text('DROP INDEX ix_tickets_assigned_engineer_id'))
    conn.execute(text('ALTER TABLE tickets DROP COLUMN assigned_engineer_id'))
    conn.commit()
    print('Old column dropped')