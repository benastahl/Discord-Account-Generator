import pickle

if __name__ == '__main__':
    with open("account_sessions.pickle", "wb") as f:
        pickle.dump({"accounts": {}}, f)
