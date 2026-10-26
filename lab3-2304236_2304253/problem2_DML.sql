USE library;

INSERT INTO AUTHOR (author_id, name, country, photo) VALUES
(1, 'Fyodor Dostoevsky', 'Russia', 'images/dostoevsky.jpg'),
(2, 'George Orwell', 'UK', 'images/orwell.jpg'),
(3, 'Ahmed Khaled Towfik', 'Egypt', 'images/towfik.jpg');

INSERT INTO BOOK (book_id, title, price, author_id, cover) VALUES
(101, 'Crime and Punishment', 15.50, 1, 'images/crime_and_punishment.jpg'),
(102, 'The Idiot', 14.00, 1, 'images/the_idiot.jpg'),
(103, '1984', 12.99, 2, 'images/1984.jpg'),
(104, 'Animal Farm', 9.50, 2, 'images/animal_farm.jpg'),
(105, 'Utopia', 10.00, 3, 'images/utopia.jpg'),
(106, 'The Legend of the Cave', 8.50, 3, 'images/cave.jpg');