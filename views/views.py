from models.models import User, Password, PasswordAnalytics
from models.algorithm import Statistics, TTests


class Response(object):

    def __init__(self, code, message, data=dict()):
        self.code = code
        self.message = message
        self.data = data

    def data_dict(self):
        return {
            'code': self.code,
            'message': self.message,
            'data': self.data
        }


class UserView(object):

    @classmethod
    def register(cls, username, fname, lname, password, timestamp_array1, timestamp_array2, timestamp_array3):

        time_array1 = []
        for i in range(len(timestamp_array1) - 1):
            time_array1.append(float(timestamp_array1[i + 1] - timestamp_array1[i])/float(1000))

        time_array2 = []
        for i in range(len(timestamp_array2) - 1):
            time_array2.append(float(timestamp_array2[i + 1] - timestamp_array2[i])/float(1000))

        time_array3 = []
        for i in range(len(timestamp_array3) - 1):
            time_array3.append(float(timestamp_array3[i + 1] - timestamp_array3[i])/float(1000))

        print(time_array1, time_array2, time_array3)
        # Create user
        User.insert_into_user(username=username, fname=fname, lname=lname)

        # Fetch user
        user = User.fetch_by_username(username=username)

        # Add new password
        Password.insert_into_passwords(userid=user.id, password=password)

        # Fetch the password
        password = Password.fetch_by_userid(userid=user.id, password=password)

        array1_sum = Statistics.sum(time_array1)
        array2_sum = Statistics.sum(time_array2)
        array3_sum = Statistics.sum(time_array3)
        total_sum = array1_sum + array2_sum + array3_sum
        total_lens = len(time_array1) + len(time_array2) + len(time_array3)

        # Insert password analytics
        PasswordAnalytics.insert_into_password_analytics(password_id=password.id, aggregate=total_sum, count=total_lens)

        return Response(code=200, message='OK')

    @classmethod
    def login(cls, username, password, timestamp_array):
        time_array = []
        for i in range(len(timestamp_array) -1):
            time_array.append(float(timestamp_array[i+1] - timestamp_array[i])/float(1000))

        print(time_array)
        # Fetch user
        user = User.fetch_by_username(username=username)

        if not user:
            return Response(code=400, message='Invalid Username')

        # Fetch Password object
        password = Password.fetch_by_userid(userid=user.id, password=password)

        if not password:
            return Response(code=400, message='Invalid Password')

        # Fetch Password Analytics
        password_analytics = PasswordAnalytics.fetch_by_password_id(password_id=password.id)

        # Get statistics of user input
        sample_stats = Statistics(data_list=time_array)
        sample_stats.compute_all()

        # Get statistics of existing inputs
        population_mean = Statistics.mean(password_analytics.aggregate, password_analytics.count)

        # Calculating the t statistic
        t_stat = TTests.t_statistic(population_mean=population_mean,
                                    sample_mean=sample_stats.data_list_mean,
                                    sample_std_deviation=sample_stats.data_list_standard_dev,
                                    sample_length=sample_stats.data_list_len_f)

        # Calculating the t distribution
        t_dist_min, t_dist_max = TTests.t_distribution(sample_length=sample_stats.data_list_len_f, alpha=0.01)

        print(t_stat, t_dist_min, t_dist_max)

        if t_stat < t_dist_min or t_stat > t_dist_max:
            return Response(code=400, message='Intrusion Detected')
        else:
            password_analytics.update_analytics(sample_stats.data_list_sum, int(sample_stats.data_list_len_f))
            return Response(code=200, message='OK')
