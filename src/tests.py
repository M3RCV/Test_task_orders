import asyncio
from aiokafka import AIOKafkaClient

async def test_connection():
    # Можно попробовать разные варианты адреса — раскомментируй нужный
    bootstrap = "localhost:9093"
    # bootstrap = "127.0.0.1:9092"
    # bootstrap = ["localhost:9092", "127.0.0.1:9092"]

    client = AIOKafkaClient(bootstrap_servers=bootstrap)

    try:
        print(f"Пытаемся подключиться к {bootstrap} ...")
        await client.bootstrap()
        print("Bootstrap прошёл успешно → хотя бы один брокер ответил")

        # Самое важное — ВЫЗОВ метода с круглыми скобками
        metadata = await client.fetch_all_metadata()

        print("\nТип полученного metadata:", type(metadata).__name__)
        print("Есть атрибут brokers?", hasattr(metadata, 'brokers'))

        if hasattr(metadata, 'brokers'):
            brokers = metadata.brokers()
            print("Тип brokers:", type(brokers).__name__)
            print("\nСписок брокеров из метаданных:")
            print(brokers)
        else:
            print("Атрибут brokers отсутствует — странная версия aiokafka?")

        # Дополнительно — топики (может быть пустой список)
        if hasattr(metadata, 'topics'):
            print("\nТопики в кластере:", list(metadata.topics))

        return True

    except Exception as e:
        print("\nОшибка:", type(e).__name__)
        print("Сообщение:", str(e))
        import traceback
        traceback.print_exc()
        return False

    finally:
        await client.close()
        print("Соединение закрыто")

# Запуск
if __name__ == "__main__":
    success = asyncio.run(test_connection())
    print("\nИтог:", "УСПЕХ ✅" if success else "ПРОВАЛ ❌")